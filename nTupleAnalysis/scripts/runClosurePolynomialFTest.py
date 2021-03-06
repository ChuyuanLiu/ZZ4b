import ROOT
ROOT.gROOT.SetBatch(True)
#ROOT.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2")
import sys
import operator
sys.path.insert(0, 'PlotTools/python/') #https://github.com/patrickbryant/PlotTools
import collections
import PlotTools
from array import array
import numpy as np
import scipy.stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

year = "RunII"
lumi = 132.6
rebin = 4

closureFileName = "ZZ4b/nTupleAnalysis/combine/hists_closure.root"

f=ROOT.TFile(closureFileName, "UPDATE")

mixes = ["3bMix4b_rWbW2_v0",
         "3bMix4b_rWbW2_v1",
         "3bMix4b_rWbW2_v2",
         "3bMix4b_rWbW2_v3",
         "3bMix4b_rWbW2_v4",
         "3bMix4b_rWbW2_v5",
         "3bMix4b_rWbW2_v6",
         ]
channels = ["zz",
            "zh",
            ]

def addYears(directory):
    hists = []
    for process in ["ttbar","multijet","data_obs"]:
        hists.append( f.Get(directory+"2016/"+process) )
        #hists[-1].SetName(process)
        hists[-1].Add(f.Get(directory+"2017/"+process))
        hists[-1].Add(f.Get(directory+"2018/"+process))
        f.mkdir(directory)
        f.cd(directory)
        hists[-1].Write()

def addMixes(directory):
    hist = f.Get(mixes[0]+"/"+directory+"/data_obs")
    #hist.SetName("data_obs")
    for mix in mixes[1:]:
        hist.Add( f.Get(mix+"/"+directory+"/data_obs") )
    f.mkdir(directory)
    f.cd(directory)
    hist.Scale(1.0/len(mixes))
    hist.Write()

for mix in mixes:
   for channel in channels:
       addYears(mix+'/'+channel)

for channel in channels:
   addMixes(channel)

f.Close()
f=ROOT.TFile(closureFileName, "UPDATE")

lps = [                                     "1",
                                        "2*x-1",
                                 "6*x^2- 6*x+1",
                        "20*x^3- 30*x^2+12*x-1",
                "70*x^4-140*x^3+ 90*x^2-20*x+1",
       "252*x^5-630*x^4+560*x^3-210*x^2+30*x-1",
       ]
lp = []
for i, s in enumerate(lps): 
    lp.append( ROOT.TF1("lp%i"%i, s, 0, 1) )


class mixedData:
    def __init__(self, directory, name):
        self.directory = directory
        self.name = name
        #self.hist = ROOT.TH1F( f.Get( self.directory+"/data_obs" ) )
        self.hist = f.Get( self.directory+"/data_obs" ).Clone()
        self.hist.SetName(str(np.random.uniform()))
        self.hist.Rebin(rebin)
        self.chi2 = None
        
    def SetBinError(self, bin, ttbar_error, multijet_error):
        data_error = self.hist.GetBinError(bin)
        total_error = (data_error**2 + ttbar_error**2 + multijet_error**2)**0.5
        self.hist.SetBinError(bin, total_error)

    def fit(self, model):
        self.hist.Fit(model, "L N0QS")
        self.chi2 = model.GetChisquare()
        self.ndf  = model.GetNDF()


class model:
    def __init__(self, directory, order=None, data_obs_name=None, mix=None):
        self.directory= directory
        f.cd(self.directory)
        #f.ls()
        self.name     = directory.replace("/","_")
        self.mix = mix
        self.ttbar    = f.Get(directory+"/ttbar")
        self.multijet = f.Get(directory+"/multijet")
        self.data_obs_name = data_obs_name if data_obs_name else directory+"/data_obs"
        #self.data_obs = ROOT.TH1F( f.Get( self.data_obs_name ) )
        self.data_obs = f.Get( self.data_obs_name ).Clone()
        self.data_obs.SetName(str(np.random.uniform()))
        self.nBins = self.data_obs.GetSize()-2 #underflow and overflow

        self.mixes=[mixedData(directory.replace(mix, otherMix), otherMix) for otherMix in mixes]

        self.background_TH1 = ROOT.TH1F("background_TH1", "", self.nBins, 0, 1)
        
        self.rebin = rebin
        self.ttbar   .Rebin(self.rebin)
        self.multijet.Rebin(self.rebin)
        self.data_obs.Rebin(self.rebin)

        self.nBins_rebin = self.data_obs.GetSize()-2

        # So that fit includes stat error from background templates, combine all stat error in quadrature
        for bin in range(1,self.nBins_rebin+1):
            data_error = self.data_obs.GetBinError(bin)
            ttbar_error = self.ttbar.GetBinError(bin)
            multijet_error = 1.0*self.multijet.GetBinError(bin)
            total_error = (data_error**2 + ttbar_error**2 + multijet_error**2)**0.5
            self.data_obs.SetBinError(bin, total_error)

            for otherMix in self.mixes: otherMix.SetBinError(bin, ttbar_error, multijet_error)

        print self.data_obs.Integral(), self.ttbar.Integral()+self.multijet.Integral()

        self.polynomials = {}
        self.background_TF1s = {}
        self.chi2s = {}
        self.ndfs = {}
        self.chi2PerNdfs = {}
        self.probs = {}
        self.parValues = {}
        self.parErrors = {}
        self.ymaxs = {}
        self.eigenVars = {}
        self.eigenPars = {}
        #self.order = 2

        if order is not None:
            self.order = order
            self.makeBackgrondTF1(order)


    def makeBackgrondTF1(self, order):
        #self.polynomials[order] = ROOT.TF1("pol"+str(order), "pol"+str(order), 0, 1)

        def background_UserFunction(xArray, pars):
            x = xArray[0]
            #self.polynomials[order].SetParameters(par)
            bin = self.ttbar.FindBin(x)
            l, u = self.ttbar.GetBinLowEdge(bin), self.ttbar.GetXaxis().GetBinUpEdge(bin)
            w = self.ttbar.GetBinWidth(bin)

            p = 1
            for i, par in enumerate(pars):
                p += par*lp[i].Integral(l,u)/w #(u-l)

            #p = self.polynomials[order].Integral(l,u)/w
            return self.ttbar.GetBinContent(bin) + p*self.multijet.GetBinContent(bin)

        self.background_TF1s[order] = ROOT.TF1 ("background_TF1_pol"+str(order), background_UserFunction, 0, 1, order+1)


    def getEigenvariations(self, order=None, debug=False):
        if order is None: order = self.order

        n = order+1
        cov = ROOT.TMatrixD(n,n)
        cor = ROOT.TMatrixD(n,n)
        for i in range(n):
            for j in range(n):
                cov[i][j] = self.fitResult.CovMatrix(i,j)
                cor[i][j] = self.fitResult.Correlation(i,j)

        if debug:
            print "Covariance Matrix:"
            cov.Print()
            print "Correlation Matrix:"
            cor.Print()

        eigenVal = ROOT.TVectorD(n)
        eigenVec = cov.EigenVectors(eigenVal)
        
        # define relative sign of eigen-basis such that the first coordinate is always positive
        for j in range(n):
            if eigenVec[0][j] >= 0: continue
            for i in range(n):
                eigenVec[i][j] *= -1

        if debug:
            print "Eigenvectors (columns)"
            eigenVec.Print()
            print "Eigenvalues"
            eigenVal.Print()

        errorVec = np.zeros((n,n), dtype=np.float)
        #errorVec = [np.array(range(n), dtype=np.float) for i in range(n)]
        for i in range(n):
            for j in range(n):
                errorVec[i,j] = eigenVec[i][j] * eigenVal[j]**0.5

        self.eigenVars[order] = errorVec

        if debug:
            print "Eigenvariations"
            for j in range(n):
                print j, errorVec[:,j]

        #get best fit parameters in eigen-basis
        eigenPar = ROOT.TMatrixD(n,1)
        eigenPar.Mult(eigenVec, ROOT.TMatrixD(n,1,self.background_TF1s[order].GetParameters()) )
        if debug:
            print "Best fit parameters in eigen-basis"
            eigenPar.Print()
        self.eigenPars[order] = np.array(range(n), dtype=np.float)
        for i in range(n):
            self.eigenPars[order][i] = eigenPar[i][0]


    def storeFitResult(self, order=None):
        if order is None: order = self.order
        self.chi2s[order] = self.background_TF1s[order].GetChisquare()
        self.ndfs[order] = self.background_TF1s[order].GetNDF()
        self.chi2PerNdfs[order] = self.chi2s[order]/self.ndfs[order]
        self.probs[order] = self.background_TF1s[order].GetProb()
        self.parValues[order] = self.background_TF1s[order].GetParameters()
        self.parErrors[order] = self.background_TF1s[order].GetParErrors()
        self.ymaxs[order] = self.background_TF1s[order].GetMaximum(0,1)


    def dumpFitResult(self, order=None):
        if order is None: order = self.order
        print "    chi^2 =",self.chi2s[order]
        print "      ndf =",self.ndfs[order]
        print "chi^2/ndf =",self.chi2PerNdfs[order]
        print "  p-value =",self.probs[order]


    def fit(self, order=None):
        if order is None: order = self.order
        if order not in self.background_TF1s: self.makeBackgrondTF1(order)            
        self.fitResult = self.data_obs.Fit(self.background_TF1s[order], "L N0QS")
        status = int(self.fitResult)
        self.getEigenvariations(order)
        self.storeFitResult(order)
        self.dumpFitResult(order)


    def fitAllMixes(self):
        fig, (ax) = plt.subplots(nrows=1)

        ax.set_title(self.name.replace("_","\_"))
        ax.set_xlabel('$\chi^2$')
        ax.set_ylabel('Arb. Units')

        chi2s = []
        markers = ['o', 'v', '^', '<', '>', 's', '*']
        colors = ['b','g','c','m']
        for i, otherMix in enumerate(self.mixes): 
            otherMix.fit(self.background_TF1s[self.order])
            chi2s.append(otherMix.chi2)
            
            kwargs = {'lw': 1,
                      'marker': markers[i%len(markers)],
                      'edgecolors': 'k',
                      'color': colors[i%len(colors)],
                      'label': otherMix.name.replace("_","\_"),
                      }

            plt.scatter(chi2s[-1], 0.0, **kwargs)

        chi2s = np.array(chi2s)
        print "chi2s.mean():",chi2s.mean(), "chi2s.std():",chi2s.std()


        x = np.linspace(scipy.stats.chi2.ppf(0.001, self.mixes[0].ndf), scipy.stats.chi2.ppf(0.999, self.mixes[0].ndf), 100)
        ax.plot(x, scipy.stats.chi2.pdf(x, self.mixes[0].ndf), 'r-', lw=2, alpha=1, label='$\chi^2$ PDF')

        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        ax.plot(xlim, [0,0], color='k', alpha=0.5, linestyle='--', linewidth=1)
        ax.set_xlim(xlim)
        ax.set_ylim([-0.005, ylim[1]])
        
        ax.legend(loc='upper right', fontsize='small', scatterpoints=1)

        name = "chi2s_"+self.name+"_rebin"+str(rebin)+".pdf"
        print "fig.savefig( "+name+" )"
        fig.savefig( name )
        plt.close(fig)


    def fTest(self, order2, order1): #order2 > order1
        for order in [order1, order2]:
            if order in self.chi2s: continue
            self.makeBackgrondTF1(order)
            self.fit(order)

        self.fStat = ( (self.chi2s[order1] - self.chi2s[order2])/(order2 - order1) ) / (self.chi2PerNdfs[order2])
        self.fProb = scipy.stats.f.cdf(self.fStat, order2-order1, self.ndfs[order2])
        print "    f(%i,%i) = %f"%(order2,order1,self.fStat)
        print "f.cdf(%i,%i) = %f"%(order2,order1,self.fProb)
        return self.fProb


    def runFTest(self):
        order = 0
        while self.fTest(order+1, order) > 0.95:
            order += 1
        print "F-Test prefers order %i over %i at only %2.0f%%"%(order+1, order, 100*self.fProb)
        self.setOrder(order)


    def setOrder(self, order):
        self.order = order
        self.background_TF1 = self.background_TF1s[order]
        self.chi2 = self.chi2s[order]
        self.ndf = self.ndfs[order]
        self.chi2PerNdf = self.chi2PerNdfs[order]
        self.prob = self.probs[order]
        self.parValue = np.array([self.parValues[order][i] for i in range(order+1)], dtype=np.float) #self.parValues[order]
        self.parError = self.parErrors[order]
        self.ymax = self.ymaxs[order]


    # def toy(self):
    #     self.data_toy = ROOT.TH1F("data_toy", "", self.nBins_rebin, 0, 1)
    #     for bin in range(1,self.nBins_rebin+1):
    #         ttbar_content, ttbar_error = self.ttbar.GetBinContent(bin), self.ttbar.GetBinError(bin)
    #         multijet_content, multijet_error = self.multijet.GetBinContent(bin), self.multijet.GetBinError(bin)
    #         total_content = ttbar_content + multijet_content
    #         total_error = (total_content + ttbar_error**2 + multijet_error**2)**0.5
    #         toy_content = np.random.normal(total_content, total_error)
    #         toy_error = (toy_content + ttbar_error**2 + multijet_error**2)**0.5
    #         self.data_toy.SetBinContent(bin, toy_content)
    #         self.data_toy.SetBinError(bin, toy_error)
    #     print "Fit Toy:"
    #     self.data_toy.Fit(self.background_TF1, "L N0")
    #     self.dumpFitResult()


    def write(self):
        f.cd(self.directory)

        for bin in range(1,self.nBins+1):
            x = self.background_TH1.GetBinCenter(bin)
            self.background_TH1.SetBinContent(bin, self.background_TF1.Eval(x)/self.rebin)

        self.background_TH1.Write()


    def plotFit(self):
        samples=collections.OrderedDict()
        samples[closureFileName] = collections.OrderedDict()
        samples[closureFileName][self.data_obs_name] = {
            "label" : ("Mixed Data %.1f/fb")%(lumi),
            "legend": 1,
            "isData" : True,
            "ratio" : "numer A",
            "color" : "ROOT.kBlack"}
        samples[closureFileName][self.directory+"/multijet"] = {
            "label" : "Multijet Model",
            "legend": 2,
            "stack" : 3,
            "ratio" : "denom A",
            "color" : "ROOT.kYellow"}
        samples[closureFileName][self.directory+"/ttbar"] = {
            "label" : "t#bar{t}",
            "legend": 3,
            "stack" : 2,
            "ratio" : "denom A",
            "color" : "ROOT.kAzure-9"}
        samples[closureFileName][self.directory+"/background_TH1"] = {
            "label" : "Fit",
            "legend": 4,
            "ratio": "denom A", 
            "color" : "ROOT.kRed"}

        if "zz" in self.directory:
            xTitle = "SvB Regressed P(ZZ)+P(ZH), P(ZZ) > P(ZH)"
        if "zh" in self.directory:
            xTitle = "SvB Regressed P(ZZ)+P(ZH), P(ZH) #geq P(ZZ)"
        parameters = {"titleLeft"   : "#bf{CMS} Internal",
                      "titleCenter" : "Signal Region",
                      "titleRight"  : "Pass #DeltaR(j,j)",
                      "maxDigits"   : 4,
                      "ratio"     : True,
                      "rMin"      : 0.9,
                      "rMax"      : 1.1,
                      "rebin"     : self.rebin,
                      "rTitle"    : "Data / Bkgd.",
                      "xTitle"    : xTitle,
                      "yTitle"    : "Events",
                      "yMax"      : self.ymax*2.0,
                      "xleg"      : [0.15, 0.15+0.33],
                      "legendSubText" : ["#bf{Fit Result:}",
                                         ],
                      "lstLocation" : "right",
                      "outputDir" : "",
                      "outputName": self.name}
        for i in range(self.order+1):
            parameters["legendSubText"] += ["#font[12]{c}_{%i} = %0.3f #pm %0.1f%%"%(i, self.parValue[i], 100*self.parError[i]/self.parValue[i])]

        parameters["legendSubText"] += ["",
                                        "#chi^{2}/DoF = %0.2f"%(self.chi2/self.ndf),
                                        "p-value = %2.0f%%"%(self.prob*100)]

        PlotTools.plot(samples, parameters, debug=False)


class ensemble:
    def __init__(self, channel, models):
        self.channel = channel
        self.models = models
        self.n = len(models)
        self.chi2s = {}
        self.ndfs = {}
        self.probs = {}
        self.fProbs = {}
        self.order = 5

    def combinedFTest(self, order2, order1):
        for order in [order1, order2]:
            self.chi2s[order], self.ndfs[order] = 0, 0
            for m in self.models:
                if order not in m.chi2s:
                    print "\n>>> ", order, m.name
                    m.makeBackgrondTF1(order)
                    m.fit(order)

                self.chi2s[order] += m.chi2s[order]
                self.ndfs[order] += m.ndfs[order]

            self.probs[order] = scipy.stats.distributions.chi2.sf(self.chi2s[order], self.ndfs[order])

        print "\n"+"#"*10
        for order in [order1, order2]:
            print " Order %i:"%order
            print "  chi2/ndf = ", self.chi2s[order]/self.ndfs[order]
            print "      prob = %2.1f%%"%(100*self.probs[order])

        fStat = ( (self.chi2s[order1] - self.chi2s[order2])/(order2 - order1)/self.n ) / (self.chi2s[order2]/self.ndfs[order2])
        self.fProbs[order1] = scipy.stats.f.cdf(fStat, (order2-order1)*self.n, self.ndfs[order2])
        print "-"*10
        print "    f(%i,%i) = %f"%(order2,order1,fStat)
        print "f.cdf(%i,%i) = %2.0f%%"%(order2,order1,100*self.fProbs[order1])
        print "#"*10

        if self.fProbs[order1] < 0.95: self.fTestSatisfied = True

        if not self.done and self.probs[order1] > 0.05 and self.fTestSatisfied:
            self.done = True
            self.order = order1
            self.prob = self.probs[order1]
            self.fProb = self.fProbs[order1]


    def runCombinedFTest(self):
        # for order in range(6):
        #     for m in self.models:
        #         if order not in m.chi2s:
        #             print "\n>>> ", order, m.name
        #             m.makeBackgrondTF1(order)
        #             m.fit(order)

        self.fTestSatisfied = False
        self.done = False
        order = -1
        while order < 4:# and (self.fProb > 0.95 or self.prob < 0.05):
            order += 1
            self.combinedFTest(order+1, order)

        if self.done:
            print "\nCombined F-Test prefers order %i over %i at %2.0f%%"%(self.order+1, self.order, 100*self.fProb)
        else:
            print "Failed to satisfy F-Test and/or goodness of fit."
            self.order = max(self.probs.iteritems(), key=operator.itemgetter(1))[0]
    
        for m in self.models:
            m.setOrder(self.order)
            m.write()
        self.getParameterDistribution()

    def fitAllMixes(self):
        for m in self.models: 
            m.fitAllMixes()
            
        fig, (ax) = plt.subplots(nrows=1)

        ax.set_title(self.channel)
        ax.set_xlabel('$\chi^2$')
        ax.set_ylabel('Arb. Units')

        chi2s = []
        markers = ['o', 'v', '^', '<', '>', 's', '*']
        colors = ['b','g','c','m']
        for i, m in enumerate(self.models): 
            chi2s.append(m.chi2)
            
            kwargs = {'lw': 1,
                      'marker': markers[i%len(markers)],
                      'edgecolors': 'k',
                      'color': colors[i%len(colors)],
                      'label': m.name.replace("_","\_"),
                      }

            plt.scatter(chi2s[-1], 0.0, **kwargs)

        chi2s = np.array(chi2s)
        print "chi2s.mean():",chi2s.mean(), "chi2s.std():",chi2s.std()


        x = np.linspace(scipy.stats.chi2.ppf(0.001, self.models[0].ndf), scipy.stats.chi2.ppf(0.999, self.models[0].ndf), 100)
        ax.plot(x, scipy.stats.chi2.pdf(x, self.models[0].ndf), 'r-', lw=2, alpha=1, label='$\chi^2$ PDF')

        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        ax.plot(xlim, [0,0], color='k', alpha=0.5, linestyle='--', linewidth=1)
        ax.set_xlim(xlim)
        ax.set_ylim([-0.005, ylim[1]])
        
        ax.legend(loc='upper right', fontsize='small', scatterpoints=1)

        name = "chi2s_"+self.channel+"_rebin"+str(rebin)+".pdf"
        print "fig.savefig( "+name+" )"
        fig.savefig( name )
        plt.close(fig)

    def getParameterDistribution(self):
        nModels = len(self.models)
        n = self.order+1
        self.parMean  = np.array([0 for i in range(n)], dtype=np.float)
        self.parMean2 = np.array([0 for i in range(n)], dtype=np.float)
        for m in self.models:
            self.parMean  += m.parValue    / nModels
            self.parMean2 += m.parValue**2 / nModels
        var = self.parMean2 - self.parMean**2
        self.parStd = var**0.5
        print "Parameter Mean:",self.parMean
        print "Parameter  Std:",self.parStd
        #cov = np.zeros((n,n))
        #for i in range(n): cov[i][i] = var[i]
        #gaussian = scipy.stats.multivariate_normal.pdf(x, mean=mean, cov=var)

        closureResults = "ZZ4b/nTupleAnalysis/combine/closureResults_%s.txt"%self.channel
        closureResultsFile = open(closureResults, 'w')
        for i in range(n):
            systUp   = "1+" #if i else ""
            systDown = "1+" #if i else ""
            cUp   = max(self.parMean[i], self.parMean[i] + self.parStd[i],  self.parStd[i])#/2
            cDown = min(self.parMean[i], self.parMean[i] - self.parStd[i], -self.parStd[i])#/2
            systUp   += "(%f)*(%s)"%(cUp,   lps[i].replace(' ',''))
            systDown += "(%f)*(%s)"%(cDown, lps[i].replace(' ',''))
            systUp   = "multijet_LP%i_%sUp   %s"%(i, channel, systUp)
            systDown = "multijet_LP%i_%sDown %s"%(i, channel, systDown)
            print systUp
            print systDown
            closureResultsFile.write(systUp+'\n')
            closureResultsFile.write(systDown+'\n')
        closureResultsFile.close()

    def plotFitResultsByOrder(self):
        fig, (ax) = plt.subplots(nrows=1)
        ax.set_ylim(0.001,1)
        ax.set_xticks(range(len(self.probs)))
        plt.yscale('log')

        x = sorted(self.fProbs.keys())
        y = [self.fProbs[o] for o in x]
        ax.plot(x, y, label='F-Test', color='black', alpha=0.8, linewidth=2)

        x = sorted(self.probs.keys())
        y = [self.probs[o] for o in x]
        ax.plot(x, y, label='Combined', color='r', linewidth=2)
        
        for m in self.models:
            x = sorted(m.probs.keys())
            y = [m.probs[o] for o in x]
            ax.plot(x, y, label=m.name.replace('_','\_'), alpha=0.5)
            
        maxOrder = x[-1]
        ax.plot([0,maxOrder], [0.05,0.05], color='k', alpha=0.5, linestyle='--', linewidth=1)
        ax.plot([0,maxOrder], [0.95,0.95], color='k', alpha=0.5, linestyle='--', linewidth=1)

        ax.set_xlabel('Polynomial Order')
        ax.set_ylabel('Fit p-value')
        ax.legend(loc='lower right', fontsize='small')

        name = "pvalues_"+channel+"_rebin"+str(rebin)+".pdf"
        print "fig.savefig( "+name+" )"
        fig.savefig( name )
        plt.close(fig)

    def plotFitResults(self, order=None):
        if order is None: order = self.order
        n = order+1

        x,y,s,c = [],[],[],[]
        x = np.concatenate( [m.eigenVars[order][0] for m in self.models] )
        if n>1: 
            y = np.concatenate( [m.eigenVars[order][1] for m in self.models] )
        if n>2:
            c = np.concatenate( [m.eigenVars[order][2] for m in self.models] )
        if n>3:
            s = np.concatenate( [m.eigenVars[order][3] for m in self.models] )

        kwargs = {'lw': 1,
                  'marker': 'o',
                  'edgecolors': 'k',
                  }
        if n>2:
            kwargs['c'] = c
            kwargs['cmap'] = 'BuPu'
        if n>3:
            s = np.array(s)
            smin = s.min()
            smax = s.max()
            srange = smax-smin
            s = s-s.min() #shift so that min is at zero
            s = s/s.max() #scale so that max is 1
            s = (s+10.0/30)*30 #shift and scale so that min is 10.0 and max is 30+10.0
            kwargs['s'] = s

        fig, (ax) = plt.subplots(nrows=1)
        ax.set_title('Fit Eigen-Variations: '+channel)
        ax.set_xlabel('c$_0$')
        ax.set_ylabel('c$_1$')
        
        plt.scatter(x, y, **kwargs)
        if 'c' in kwargs:
            cbar = plt.colorbar(label='c$_2$',
                                #use_gridspec=False, location="top"
                                ) 

        if 's' in kwargs:
            #lt = plt.scatter([],[], s=0,    lw=0, edgecolors='none',  facecolors='none')
            l1 = plt.scatter([],[], s=(0.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')
            l2 = plt.scatter([],[], s=(1.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')
            l3 = plt.scatter([],[], s=(2.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')
            l4 = plt.scatter([],[], s=(3.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')

            handles = [#lt,
                       l1,
                       l2,
                       l3,
                       l4]
            labels = [#"p$_3$",
                      "%0.2f"%smin,
                      "%0.2f"%(smin+srange*1.0/3),
                      "%0.2f"%(smin+srange*2.0/3),
                      "%0.2f"%smax,
                     ]

            leg = plt.legend(handles, labels, 
                             ncol=1, 
                             fontsize='medium',
                             #frameon=False, #fancybox=False, edgecolor='black',
                             #markerfirst=False,
                             #bbox_to_anchor=(1.22, 1), loc='upper left',
                             loc='best',
                             #handlelength=0.8, #handletextpad=1, #borderpad = 0.5,
                             title='c$_3$', 
                             #title_fontsize='small',
                             #columnspacing=1.8,
                             #labelspacing=1.5,
                             scatterpoints = 1, 
                             #scatteryoffsets=[0.5],
                             )

        
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        ax.plot(xlim, [0,0], color='k', alpha=0.5, linestyle='--', linewidth=1)
        ax.plot([0,0], ylim, color='k', alpha=0.5, linestyle='--', linewidth=1)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        
        name = 'eigenvariations_'+channel+'.pdf'
        print "fig.savefig( "+name+" )"
        fig.savefig( name )
        plt.close(fig)


        #plot fit parameters
        x,y,s,c = [],[],[],[]
        for m in self.models:
            x.append( m.parValues[order][0] )
            if n>1:
                y.append( m.parValues[order][1] )
            if n>2:
                c.append( m.parValues[order][2] )
            if n>3:
                s.append( m.parValues[order][3] )

        x = np.array(x)
        y = np.array(y)
    
        kwargs = {'lw': 1,
                  'marker': 'o',
                  'edgecolors': 'k',
                  }
        if n>2:
            kwargs['c'] = c
            kwargs['cmap'] = 'BuPu'
        if n>3:
            s = np.array(s)
            smin = s.min()
            smax = s.max()
            srange = smax-smin
            s = s-s.min() #shift so that min is at zero
            s = s/s.max() #scale so that max is 1
            s = (s+10.0/30)*30 #shift and scale so that min is 10.0 and max is 30+10.0
            kwargs['s'] = s

        fig, (ax) = plt.subplots(nrows=1)
        ax.set_aspect(1)
        ax.set_title('Legendre Polynomial Coefficients: '+channel)
        ax.set_xlabel('c$_0$')
        ax.set_ylabel('c$_1$')

        #generate a ton of random points on a hypersphere in dim=n so surface is dim=n-1.
        points  = np.random.uniform(0,1,(n,100**(n-1))) # random points in a hypercube
        points /= np.linalg.norm(points, axis=0) # normalize them to the hypersphere surface
        
        # for each model, find the point which maximizes the change in c_0**2 + c_1**2
        maxr=np.zeros((2, len(x)), dtype=np.float)
        minr=np.zeros((2, len(x)), dtype=np.float)
        for i, m in enumerate(self.models):
            eigenVars = m.eigenVars[order]
            plane = np.matmul( eigenVars[0:min(n,2),:], points )
            r2 = plane[0]**2
            if n>1:
                r2 += plane[1]**2
            
            maxr[:,i] = plane[:,r2==r2.max()].T[0]
            
            #construct orthogonal unit vector to maxr
            minrvec = np.copy(maxr[::-1,i])
            minrvec[0] *= -1
            minrvec /= np.linalg.norm(minrvec)
            
            #find maxr along minrvec to get minr
            dr2 = np.matmul( minrvec, plane )**2
            #minr[:,i] = plane[:,dr2==dr2.max()].T[0]#this guy is the ~right length but might be slightly off orthogonal
            minr[:,i] = minrvec * dr2.max()**0.5#this guy is the ~right length and is orthogonal by construction
            

        print maxr
        print minr
        ax.quiver(x, y,  maxr[0],  maxr[1], scale_units='xy', angles='xy', scale=1, width=0.002)
        ax.quiver(x, y, -maxr[0], -maxr[1], scale_units='xy', angles='xy', scale=1, width=0.002)

        ax.quiver(x, y,  minr[0],  minr[1], scale_units='xy', angles='xy', scale=1, width=0.002)
        ax.quiver(x, y, -minr[0], -minr[1], scale_units='xy', angles='xy', scale=1, width=0.002)

        
        plt.scatter(x, y, **kwargs)


        if 'c' in kwargs:
            cbar = plt.colorbar(label='c$_2$',
                                #use_gridspec=False, location="top"
                                ) 

        if 's' in kwargs:
            #lt = plt.scatter([],[], s=0,    lw=0, edgecolors='none',  facecolors='none')
            l1 = plt.scatter([],[], s=(0.0/3+10.0/30)*30,  lw=1, edgecolors='black', facecolors='none')
            l2 = plt.scatter([],[], s=(1.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')
            l3 = plt.scatter([],[], s=(2.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')
            l4 = plt.scatter([],[], s=(3.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')

            handles = [#lt,
                       l1,
                       l2,
                       l3,
                       l4]
            labels = [#"p$_3$",
                      "%0.2f"%smin,
                      "%0.2f"%(smin+srange*1.0/3),
                      "%0.2f"%(smin+srange*2.0/3),
                      "%0.2f"%smax,
                     ]

            leg = plt.legend(handles, labels, 
                             ncol=1, 
                             fontsize='medium',
                             #frameon=False, #fancybox=False, edgecolor='black',
                             #markerfirst=False,
                             #bbox_to_anchor=(1.22, 1), loc='upper left',
                             loc='best',
                             #handlelength=0.8, #handletextpad=1, #borderpad = 0.5,
                             title='c$_3$', 
                             #title_fontsize='small',
                             #columnspacing=1.8,
                             #labelspacing=1.5,
                             scatterpoints = 1, 
                             #scatteryoffsets=[0.5],
                             )

        
        #xlim, ylim = ax.get_xlim(), ax.get_ylim()
        xlim, ylim = [-0.1,0.1], [-0.1,0.1]
        ax.plot(xlim, [0,0], color='k', alpha=0.5, linestyle='--', linewidth=1)
        ax.plot([0,0], ylim, color='k', alpha=0.5, linestyle='--', linewidth=1)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        
        name = 'fitParameters_'+channel+'.pdf'
        print "fig.savefig( "+name+" )"
        fig.savefig( name )
        plt.close(fig)


        # x,y,s,c = [],[],[],[]
        # for m in self.models:
        #     x.append( m.eigenPars[order][0] )
        #     if n>1:
        #         y.append( m.eigenPars[order][1] )
        #     if n>2:
        #         c.append( m.eigenPars[order][2] )
        #     if n>3:
        #         s.append( m.eigenPars[order][3] )

        # kwargs = {'lw': 1,
        #           'marker': 'o',
        #           'edgecolors': 'k',
        #           }
        # if n>2:
        #     kwargs['c'] = c
        #     kwargs['cmap'] = 'BuPu'
        # if n>3:
        #     s = np.array(s)
        #     smin = s.min()
        #     smax = s.max()
        #     srange = smax-smin
        #     s = s-s.min() #shift so that min is at zero
        #     s = s/s.max() #scale so that max is 1
        #     s = (s+10.0/30)*30 #shift and scale so that min is 10.0 and max is 30+10.0
        #     kwargs['s'] = s

        # fig, (ax) = plt.subplots(nrows=1)
        # ax.set_title('Fit Parameters (Eigen-Basis): '+channel)
        # ax.set_xlabel('e$_0$')
        # ax.set_ylabel('e$_1$')
        
        # plt.scatter(x, y, **kwargs)
        # if 'c' in kwargs:
        #     cbar = plt.colorbar(label='e$_2$',
        #                         ticks=np.linspace(0.25, -1, 1, endpoint=True)
        #                         #use_gridspec=False, location="top"
        #                         ) 

        # if 's' in kwargs:
        #     #lt = plt.scatter([],[], s=0,    lw=0, edgecolors='none',  facecolors='none')
        #     l1 = plt.scatter([],[], s=(0.0/3+10.0/30)*30,  lw=1, edgecolors='black', facecolors='none')
        #     l2 = plt.scatter([],[], s=(1.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')
        #     l3 = plt.scatter([],[], s=(2.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')
        #     l4 = plt.scatter([],[], s=(3.0/3+10.0/30)*30, lw=1, edgecolors='black', facecolors='none')

        #     handles = [#lt,
        #                l1,
        #                l2,
        #                l3,
        #                l4]
        #     labels = [#"p$_3$",
        #               "%0.2f"%smin,
        #               "%0.2f"%(smin+srange*1.0/3),
        #               "%0.2f"%(smin+srange*2.0/3),
        #               "%0.2f"%smax,
        #              ]

        #     leg = plt.legend(handles, labels, 
        #                      ncol=1, 
        #                      fontsize='medium',
        #                      #frameon=False, #fancybox=False, edgecolor='black',
        #                      #markerfirst=False,
        #                      #bbox_to_anchor=(1.22, 1), loc='upper left',
        #                      loc='best',
        #                      #handlelength=0.8, #handletextpad=1, #borderpad = 0.5,
        #                      title='e$_3$', 
        #                      #title_fontsize='small',
        #                      #columnspacing=1.8,
        #                      #labelspacing=1.5,
        #                      scatterpoints = 1, 
        #                      #scatteryoffsets=[0.5],
        #                      )

        
        # xlim, ylim = ax.get_xlim(), ax.get_ylim()
        # xlim, ylim = [-1,1], [-1,1]
        # ax.plot(xlim, [0,0], color='k', alpha=0.5, linestyle='--', linewidth=1)
        # ax.plot([0,0], ylim, color='k', alpha=0.5, linestyle='--', linewidth=1)
        # ax.set_xlim(xlim)
        # ax.set_ylim(ylim)
        
        # name = 'fitParameters_eigenbasis_'+channel+'.pdf'
        # print "fig.savefig( "+name+" )"
        # fig.savefig( name )



models = {}

for channel in channels:    
    models[channel] = []
    for i, mix in enumerate(mixes):
        models[channel].append( model(mix+"/"+channel, data_obs_name=channel+"/data_obs", mix=mix) )
        #models[channel][i].fit(order=2)
        #print "Single F-Test:", channel, i
        #models[channel][i].runFTest()
        #models[channel][i].write()
    print "-"*20
    print "Combined F-Test:", channel
    allMixes = ensemble(channel, models[channel])
    allMixes.runCombinedFTest()
    print "-"*20
    allMixes.plotFitResultsByOrder()
    allMixes.plotFitResults()
    allMixes.fitAllMixes()

f.Close()

for channel in channels:
    for i, mix in enumerate(mixes):
        models[channel][i].plotFit()


