
import sys
sys.path.insert(0, 'nTupleAnalysis/python/') #https://github.com/patrickbryant/nTupleAnalysis
from commandLineHelpers import *
import optparse

parser = optparse.OptionParser()
parser.add_option('-e',            action="store_true", dest="execute",        default=False, help="Execute commands. Default is to just print them")
parser.add_option('-y',                                 dest="year",      default="2018,2017,2016", help="Year or comma separated list of years")
parser.add_option('-w',            action="store_true", dest="doWeights",      default=False, help="Fit jetCombinatoricModel and nJetClassifier TSpline")
parser.add_option('--histsForJCM',  action="store_true",      help="Make hist.root for JCM")
parser.add_option('--histsWithJCM', action="store_true",      help="Make hist.root with JCM")
parser.add_option('--histsWithFvT', action="store_true",      help="Make hist.root with FvT")
parser.add_option('--histsWithNoFvT', action="store_true",      help="Make hist.root with FvT")
parser.add_option('--plotsWithFvT', action="store_true",      help="Make pdfs with FvT")
parser.add_option('--plotsWithNoFvT', action="store_true",      help="Make pdfs with FvT")
parser.add_option('--plotsWithJCM', action="store_true",      help="Make pdfs with JCM")
parser.add_option('--copyToEOS',  action="store_true",      help="Copy 3b subsampled data to eos ")
parser.add_option('--cleanPicoAODs',  action="store_true",      help="rm 3b subsampled data  ")
parser.add_option('--cutFlowBeforeJCM', action="store_true",      help="Make 4b cut flow before JCM")
parser.add_option('--moveFinalPicoAODsToEOS', action="store_true",      help="Move Final AODs to EOS")
parser.add_option('--cleanFinalPicoAODsToEOS', action="store_true",      help="Move Final AODs to EOS")
parser.add_option('-c',   '--condor',   action="store_true", default=False,           help="Run on condor")
parser.add_option('--email',            default=None,      help="")

o, a = parser.parse_args()


doRun = o.execute



#
# In the following "3b" refers to 3b subsampled to have the 4b statistics
#
#outputDir="/uscms/home/jda102/nobackup/HH4b/CMSSW_11_1_3/src/closureTests/nominal"
#outputDirComb="/uscms/home/jda102/nobackup/HH4b/CMSSW_11_1_3/src/closureTests/combined"
#outputDir="/uscms/home/jda102/nobackup/HH4b/CMSSW_10_2_0/src/closureTests/nominal"
#outputDirComb="/uscms/home/jda102/nobackup/HH4b/CMSSW_10_2_0/src/closureTests/combined"

outputDir="closureTests/nominal/"
outputDirComb="closureTests/combined/"


# Helpers
runCMD='nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py'
weightCMD='python ZZ4b/nTupleAnalysis/scripts/makeWeights.py'

ttbarSamples = ["TTToHadronic","TTToSemiLeptonic","TTTo2L2Nu"]


years = o.year.split(",")

yearOpts = {}
#yearOpts["2018"]=' -y 2018 --bTag 0.2770 '
#yearOpts["2017"]=' -y 2017 --bTag 0.3033 '
#yearOpts["2016"]=' -y 2016 --bTag 0.3093 '
yearOpts["2018"]=' -y 2018 --bTag 0.6 '
yearOpts["2017"]=' -y 2017 --bTag 0.6 '
yearOpts["2016"]=' -y 2016 --bTag 0.6 '


MCyearOpts = {}
MCyearOpts["2018"]=yearOpts["2018"]+' --bTagSF -l 60.0e3 --isMC '
MCyearOpts["2017"]=yearOpts["2017"]+' --bTagSF -l 36.7e3 --isMC '
MCyearOpts["2016"]=yearOpts["2016"]+' --bTagSF -l 35.9e3 --isMC '

plotOpts = {}
plotOpts["2018"]=" -l 60.0e3 -y 2018"
plotOpts["2017"]=" -l 36.7e3 -y 2017"
plotOpts["2016"]=" -l 35.9e3 -y 2016"
plotOpts["RunII"]=" -l 132.6e3 -y RunII"

from condorHelpers import *

CMSSW = getCMSSW()
USER = getUSER()
EOSOUTDIR = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/nominal/"
TARBALL   = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/"+CMSSW+".tgz"



#tagID = "b0p6"
tagID = "b0p60p3"


def getOutDir():
    if o.condor:
        return EOSOUTDIR
    return outputDir


if o.condor:
    print "Making Tarball"
    makeTARBALL(o.execute)


# 
#  Make Hists for JCM Calc
#
if o.histsForJCM: 

    #
    #  Make Hists
    #
    cmds = []
    logs = []
    dag_config = []
    condor_jobs = []

    histName = "hists_"+tagID+".root "
    histOut = " --histFile "+histName
    
    for y in years:
        picoOut = " -p picoAOD_"+tagID+".root "
        h10 = " --histogramming 10 --histDetail 7 "    


        cmd = runCMD+"  -i "+outputDir+"/fileLists/data"+y+"_"+tagID+".txt "+picoOut+" -o "+outputDir+" "+ yearOpts[y] + h10 + histOut 

        if o.condor:
            cmd += " --condor"
            condor_jobs.append(makeCondorFile(cmd, EOSOUTDIR, "data"+y+"_"+tagID, outputDir=outputDir, filePrefix="histsForJCM_"))
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_data"+y+"_"+tagID)


        #
        #  Make Hists for ttbar
        #
        for tt in ttbarSamples:
            cmd = runCMD+" -i "+outputDir+"/fileLists/"+tt+y+"_noMjj_"+tagID+".txt "+ picoOut +" -o "+outputDir+ MCyearOpts[y] + h10 + histOut 

            if o.condor:
                cmd += " --condor"
                condor_jobs.append(makeCondorFile(cmd, EOSOUTDIR, tt+y+"_noMjj_"+tagID, outputDir=outputDir, filePrefix="histsForJCM_"))
            else:
                cmds.append(cmd)
                logs.append(outputDir+"/log_"+tt+y+"_"+tagID)


    if o.condor:
        dag_config.append(condor_jobs)
    else:
        babySit(cmds, doRun, logFiles=logs)

    #
    #  Hadd ttbar
    #
    cmds = [] 
    logs = []
    condor_jobs = []
    
    histName = "hists_"+tagID+".root " 

    for y in years:
        mkdir(outputDir+"/TT"+y, doRun)
        
        cmd = "hadd -f "
        if not o.condor: cmd += outputDir+"/TT"+y+"/"
        cmd += histName+" "

        for tt in ttbarSamples:        
            cmd += getOutDir()+"/"+tt+y+"_noMjj_"+tagID+"/"+histName

        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, EOSOUTDIR, "TT"+y, outputDir=outputDir, filePrefix="histsForJCM_"))            
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_HaddTT"+y+"_"+tagID)

    if o.condor:
        dag_config.append(condor_jobs)
    else:
        babySit(cmds, doRun, logFiles=logs)


    #
    #   Hadd years
    #
    if "2016" in years and "2017" in years and "2018" in years:
    
        mkdir(outputDir+"/dataRunII", doRun)
        mkdir(outputDir+"/TTRunII",   doRun)

        cmds = []
        logs = []
        condor_jobs = []        
    
        histName = "hists_"+tagID+".root " 
    
        cmd = "hadd -f "
        if not o.condor: cmd += outputDir+"/dataRunII/"
        cmd += histName+" "

        for y in years:
            cmd += getOutDir()+"/data"+y+"_"+tagID+"/"+histName+" "

        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, EOSOUTDIR, "dataRunII", outputDir=outputDir, filePrefix="histsForJCM_"))            
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_haddDataRunII_beforeJCM_"+tagID)


        cmd = "hadd -f "
        if not o.condor: cmd += outputDir+"/TTRunII/"
        cmd += histName+" "
            
        for y in years:
            cmd += getOutDir()+"/TT"+y+"/"  +histName+" "

        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, EOSOUTDIR, "TTRunII", outputDir=outputDir, filePrefix="histsForJCM_"))            
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_haddTTRunII_beforeJCM_"+tagID)

        if o.condor:
            dag_config.append(condor_jobs)            
        else:
            babySit(cmds, doRun, logFiles=logs)



    if o.condor:
        rmdir(outputDir+"histsForJCM_All.dag", doRun)
        rmdir(outputDir+"histsForJCM_All.dag.*", doRun)


        dag_file = makeDAGFile("histsForJCM_All.dag",dag_config, outputDir=outputDir)
        cmd = "condor_submit_dag "+dag_file
        execute(cmd, o.execute)

    else:
        if o.email: execute('echo "Subject: [makeClosureNominal] mixInputs  Done" | sendmail '+o.email,doRun)





#
#  Cut flow to comp TTBar Fraction
#
if o.cutFlowBeforeJCM:
    cmds = []
    logs = []

    yearsToPlot = years
    if "2016" in years and "2017" in years and "2018" in years:
        yearsToPlot.append("RunII")

    histName = "hists_"+tagID+".root"
    for y in years:
    
        #
        # MAke Plots
        #
        dataFile  = outputDir+"/data"+y+"/"+histName #if not y == "RunII" else outputDir+"/data"+y+"/"+histName
        ttbarFile = outputDir+"/TT"+y+"/"+histName

        cmd = "python ZZ4b/nTupleAnalysis/scripts/makeCutFlow.py "
        cmd += " --d4 "+dataFile
        cmd += " --d3 "+dataFile
        cmd += " --t4 "+ttbarFile
        cmd += " --t3 "+ttbarFile
        cmd += " --name "+outputDir+"/CutFlow_beforeJCM_"+y+"_"+tagID
        cmd += " --makePDF "
        cmds.append(cmd)
        logs.append(outputDir+"/log_cutFlow_beforeJCM_"+y)

    
    babySit(cmds, doRun, logFiles=logs)    
    
    cmds = []
    for y in years:
        cmds.append("mv CutFlow_beforeJCM_"+y+"_"+tagID+".pdf "+outputDir+"/")
            
    babySit(cmds, doRun)    


#
#  Fit JCM
#
if o.doWeights:
    
    cmds = []
    logs = []

    mkdir(outputDir+"/weights", doRun)

    yearsToFit = years
    if "2016" in years and "2017" in years and "2018" in years:
        yearsToFit.append("RunII")

    histName = "hists_"+tagID+".root " 

    for y in yearsToFit:

        dataFile  = getOutDir()+"/data"+y+"_"+tagID+"/"+histName if not y == "RunII" else getOutDir()+"/data"+y+"/"+histName
        ttbarFile = getOutDir()+"/TT"+y+"/"+histName

        cmd = weightCMD
        cmd += " -d "+dataFile
        cmd += " --tt "+ttbarFile
        cmd += " -c passMDRs   -o "+outputDir+"/weights/data"+y+"_"+tagID+"/  -r SB -w 01-00-00 "+plotOpts[y]
        
        cmds.append(cmd)
        logs.append(outputDir+"/log_JCM"+y+"_"+tagID)
    
    babySit(cmds, doRun, logFiles=logs)
    
    rmTARBALL(o.execute)


#
#  Copy PicoAODs to EOS
#
if o.copyToEOS:

    def copy(fileName, subDir, outFileName):
        cmd  = "xrdcp  "+fileName+" root://cmseos.fnal.gov//store/user/johnda/closureTest/nominal/"+subDir+"/"+outFileName
    
        if doRun:
            os.system(cmd)
        else:
            print cmd


    for y in years:
        for tt in ["data","TTTo2L2Nu","TTToHadronic","TTToSemiLeptonic"]:
            subDir = tt+y if tt == "data" else tt+y+"_noMjj"
            copy("closureTests/nominal/"+subDir+"_"+tagID+"/picoAOD_"+tagID+".root", subDir,"picoAOD_"+tagID+".root")

#
#  cleanup
#
if o.cleanPicoAODs:
    
    def rm(fileName):
        cmd  = "rm  "+fileName
    
        if doRun: os.system(cmd)
        else:     print cmd

    for y in years:
        for tt in ["data","TTTo2L2Nu","TTToHadronic","TTToSemiLeptonic"]:
            subDir = tt+y if tt == "data" else tt+y+"_noMjj"
            rm("closureTests/nominal/"+subDir+"_"+tagID+"/picoAOD_"+tagID+".root")



#
#  Adding JCM weights now done in makeClosureTestCombined
#



#
#  Make 3b Hists with JCM weights applied
#
if o.histsWithJCM: 

    #
    #  Make Hists
    #
    cmds = []
    logs = []

    JCMName="Nominal"
    histName = "hists_3b_wJCM_"+JCMName+".root "
    histOut = " --histFile "+histName

    for y in years:

        pico3b = "picoAOD_3b_wJCM.root"
        picoOut = " -p NONE "
        h10 = " --histogramming 10 --histDetail 7 "    

        cmds.append(runCMD+" -i "+outputDirComb+"/data"+y+"/"+pico3b+             picoOut  +   yearOpts[y]+ h10 + histOut + " --jcmNameLoad "+JCMName)    #outputDir+"/log_"+y+"_wJCM_wFVT
        cmds.append(runCMD+" -i "+outputDirComb+"/TTToHadronic"+y+"/"+pico3b+     picoOut  + MCyearOpts[y]+ h10 + histOut + " --jcmNameLoad "+JCMName)    #outputDir+"/log_TTHad"+y+"_wJCM_wFVT
        cmds.append(runCMD+" -i "+outputDirComb+"/TTToSemiLeptonic"+y+"/"+pico3b+ picoOut  + MCyearOpts[y]+ h10 + histOut + " --jcmNameLoad "+JCMName)    #outputDir+"/log_TTSem"+y+"_wJCM_wFVT
        cmds.append(runCMD+" -i "+outputDirComb+"/TTTo2L2Nu"+y+"/"+pico3b+        picoOut  + MCyearOpts[y]+ h10 + histOut + " --jcmNameLoad "+JCMName)    #outputDir+"/log_TT2L2Nu"+y+"_wJCM_wFVT
        
    babySit(cmds, doRun)

    
    #
    #  Hadd TTbar
    #
    cmds = []

    for y in years:
        cmds.append("hadd -f "+outputDir+"/TT"+y+"/"+histName+" "+outputDirComb+"/TTToHadronic"+y+"/"+histName+"  "+outputDirComb+"/TTToSemiLeptonic"+y+"/"+histName+" "+outputDirComb+"/TTTo2L2Nu"+y+"/"+histName)

    babySit(cmds, doRun)


    #
    # Subtract QCD 
    #
    cmds = []
    for y in years:
        mkdir(outputDir+"/QCD"+y, doRun)

        cmd = "python ZZ4b/nTupleAnalysis/scripts/subtractTT.py "
        cmd += " -d "+outputDirComb+"/data"+y+"/"+histName
        cmd += " -tt "+outputDirComb+"/TT"+y+"/"+histName
        cmd += " -q "+outputDir+"/QCD"+y+"/"+histName
        cmds.append(cmd)
        
    babySit(cmds, doRun)    



#
#  Make CutFlows
#
if o.plotsWithJCM:
    cmds = []
    for y in years:
            
        histName4b="hists_4b.root" 

        JCMName="Nominal"
        histName3b = "hists_3b_wJCM_"+JCMName+".root "

        cmd = "python ZZ4b/nTupleAnalysis/scripts/makeCutFlow.py "
        cmd += " --d4 "+outputDir+"/data"+y+"/"+histName4b
        cmd += " --d3 "+outputDirComb+"/data"+y+"/"+histName3b
        cmd += " --t4 "+outputDir+"/TT"+y+"/"+histName4b
        cmd += " --t3 "+outputDirComb+"/TT"+y+"/"+histName3b
        cmd += " --t4_s "+outputDir+"/TTToSemiLeptonic"+y+"/"+histName4b
        cmd += " --t4_h "+outputDir+"/TTToHadronic"+y+"/"+histName4b
        cmd += " --t4_d "+outputDir+"/TTTo2L2Nu"+y+"/"+histName4b
        cmd += " --t3_s "+outputDirComb+"/TTToSemiLeptonic"+y+"/"+histName3b
        cmd += " --t3_h "+outputDirComb+"/TTToHadronic"+y+"/"+histName3b
        cmd += " --t3_d "+outputDirComb+"/TTTo2L2Nu"+y+"/"+histName3b
        cmd += " --name "+outputDir+"/CutFlow_wJCM_"+y
        cmd += " --makePDF"
        cmds.append(cmd)

        #
        # MAke Plots
        #
        cmd = "python ZZ4b/nTupleAnalysis/scripts/makePlots.py -o "+outputDir+" -p plotsWithJCM_"+y+ plotOpts[y]+" -m -j  --noSignal "
        cmd += " --qcd "+outputDir+"/QCD"+y+"/"+histName3b    
        cmd += " --data "+outputDir+"/data"+y+"/"+histName4b
        cmd += " --TT "+outputDir+"/TT"+y+"/"+histName4b
        cmds.append(cmd)

    babySit(cmds, doRun)    

    cmds = []
    for y in years:
        cmds.append("tar -C "+outputDir+" -zcf "+outputDir+"/plotsWithJCM_"+y+".tar plotsWithJCM"+y)
    babySit(cmds, doRun)    


#
#  Training  done seperately
#



#
#  Make Hists with JCM and FvT weights applied
#
if o.histsWithFvT: 

    #
    #  Make Hists
    #
    cmds = []
    logs = []
    dag_config = []
    condor_jobs = []

    JCMName="Nominal"
    FvTName="_Nominal"

    histName3b = "hists_3b_wJCM_"+JCMName+"_wFVT"+FvTName+"_"+tagID+".root "
    histName4b = "hists_4b_wFVT"+FvTName+"_"+tagID+".root "

    picoOut = " -p NONE "
    h10 = " --histogramming 10 --histDetail 9 "    
    histOut3b = " --histFile "+histName3b
    histOut4b = " --histFile "+histName4b
    outDir = " -o "+getOutDir()+" "

    for y in years:

        #
        # 3b
        #
        inputFile = " -i "+outputDirComb+"/fileLists/data"+y+"_"+tagID+"_3b_wFvT.txt "
        
        cmd = runCMD + inputFile + outDir + picoOut  +   yearOpts[y]+ h10 + histOut3b + " --jcmNameLoad "+JCMName+ " -r --FvTName "+FvTName
        
        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, "None", "data"+y+"_"+tagID, outputDir=outputDir, filePrefix="histsWithFvT_3b_"))
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_"+y+"_3b_wJCM_wFVT_"+tagID)

        for tt in ttbarSamples:
            inputFile = " -i "+outputDirComb+"/fileLists/"+tt+y+"_"+tagID+"_3b_wFvT.txt "

            cmd = runCMD + inputFile  + outDir + picoOut  + MCyearOpts[y] + h10 + histOut3b + " --jcmNameLoad "+JCMName+ " -r --FvTName "+FvTName

            if o.condor:
                condor_jobs.append(makeCondorFile(cmd, "None", tt+y+"_"+tagID, outputDir=outputDir, filePrefix="histsWithFvT_3b_"))
            else:
                cmds.append(cmd)
                logs.append(outputDir+"/log_"+tt+y+"_3b_wJCM_wFVT_"+tagID)


        #
        # 4b
        #
        inputFile = " -i "+outputDirComb+"/fileLists/data"+y+"_"+tagID+"_4b_wFvT.txt "

        cmd = runCMD + inputFile + outDir + picoOut  +   yearOpts[y]+ h10 + histOut4b + " -r --FvTName "+FvTName

        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, "None", "data"+y+"_"+tagID, outputDir=outputDir, filePrefix="histsWithFvT_4b_"))
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_"+y+"_4b_wFVT_"+tagID)

        for tt in ttbarSamples:
            inputFile = " -i "+outputDirComb+"/fileLists/"+tt+y+"_"+tagID+"_4b_wFvT.txt "

            cmd = runCMD + inputFile + outDir + picoOut  + MCyearOpts[y]+ h10 + histOut4b + " -r --FvTName "+FvTName

            if o.condor:
                condor_jobs.append(makeCondorFile(cmd, "None", tt+y+"_"+tagID, outputDir=outputDir, filePrefix="histsWithFvT_4b_"))
            else:
                cmds.append(cmd)
                logs.append(outputDir+"/log_"+tt+y+"_4b_wFVT_"+tagID)

    if o.condor:
        dag_config.append(condor_jobs)
    else:        
        babySit(cmds, doRun, logFiles=logs)

    
    #
    #  Hadd TTbar
    #
    cmds = []
    logs = []
    condor_jobs = []

    for y in years:
        cmd = "hadd -f "+getOutDir()+"/TT"+y+"/"+histName3b+" "+getOutDir()+"/TTToHadronic"+y+"_"+tagID+"_3b_wFvT/"+histName3b+"  "+getOutDir()+"/TTToSemiLeptonic"+y+"_"+tagID+"_3b_wFvT/"+histName3b+" "+getOutDir()+"/TTTo2L2Nu"+y+"_"+tagID+"_3b_wFvT/"+histName3b
        
        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, "None", "TT"+y, outputDir=outputDir, filePrefix="histsWithFvT_3b_"))
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_haddTT_3b_wJCM_wFvT_"+y+"_"+tagID)


        cmd = "hadd -f "+getOutDir()+"/TT"+y+"/"+histName4b+" "+getOutDir()+"/TTToHadronic"+y+"_"+tagID+"_4b_wFvT/"+histName4b+"  "+getOutDir()+"/TTToSemiLeptonic"+y+"_"+tagID+"_4b_wFvT/"+histName4b+" "+getOutDir()+"/TTTo2L2Nu"+y+"_"+tagID+"_4b_wFvT/"+histName4b
        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, "None", "TT"+y, outputDir=outputDir, filePrefix="histsWithFvT_4b_"))
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_haddTT_4b_wFvT_"+y+"_"+tagID)

    if o.condor:
        dag_config.append(condor_jobs)
    else: 
        babySit(cmds, doRun, logFiles=logs)


    #
    #   Hadd years
    #
    if "2016" in years and "2017" in years and "2018" in years:
    
        mkdir(outputDir+"/dataRunII", doRun)
        mkdir(outputDir+"/TTRunII",   doRun)

        cmds = []
        logs = []
        condor_jobs = []        

        cmd = "hadd -f "+getOutDir()+"/dataRunII/"+histName3b+" "+getOutDir()+"/data2016_"+tagID+"_3b_wFvT/"+histName3b+" "+getOutDir()+"/data2017_"+tagID+"_3b_wFvT/"+histName3b+" "+getOutDir()+"/data2018_"+tagID+"_3b_wFvT/"+histName3b
        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, "None", "dataRunII", outputDir=outputDir, filePrefix="histsWithFvT_3b_"))            
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_haddDataRunII_3b_"+tagID)

        cmd = "hadd -f "+getOutDir()+"/dataRunII/"+histName4b+" "+getOutDir()+"/data2016_"+tagID+"_4b_wFvT/"+histName4b+" "+getOutDir()+"/data2017_"+tagID+"_4b_wFvT/"+histName4b+" "+getOutDir()+"/data2018_"+tagID+"_4b_wFvT/"+histName4b
        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, "None", "dataRunII", outputDir=outputDir, filePrefix="histsWithFvT_4b_"))            
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_haddDataRunII_4b_"+tagID)

        cmd = "hadd -f "+getOutDir()+"/TTRunII/"  +histName4b+" "+getOutDir()+"/TT2016/"  +histName4b+" "+getOutDir()+"/TT2017/"  +histName4b+" "+getOutDir()+"/TT2018/"  +histName4b

        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, "None", "TTRunII", outputDir=outputDir, filePrefix="histsWithFvT_4b_"))            
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_haddDataRunII_TT_"+tagID)

        cmd = "hadd -f "+getOutDir()+"/TTRunII/"  +histName3b+" "+getOutDir()+"/TT2016/"  +histName3b+" "+getOutDir()+"/TT2017/"  +histName3b+" "+getOutDir()+"/TT2018/"  +histName3b

        if o.condor:
            condor_jobs.append(makeCondorFile(cmd, "None", "TTRunII", outputDir=outputDir, filePrefix="histsWithFvT_3b_"))            
        else:
            cmds.append(cmd)
            logs.append(outputDir+"/log_haddDataRunII_TT_3b_"+tagID)

        if o.condor:
            dag_config.append(condor_jobs)
        else: 
            babySit(cmds, doRun, logFiles=logs)

    if o.condor:
        execute("rm "+outputDir+"histsWithFvT_All.dag", doRun)
        execute("rm "+outputDir+"histsWithFvT_All.dag.*", doRun)


        dag_file = makeDAGFile("histsWithFvT_All.dag",dag_config, outputDir=outputDir)
        cmd = "condor_submit_dag "+dag_file
        execute(cmd, o.execute)

    else:
        if o.email: execute('echo "Subject: [makeClosureNominal] histsWithFvT Done" | sendmail '+o.email,doRun)




#
#  Make CutFlows
#
if o.plotsWithFvT:
    cmds = []
    logs = []
    
    yearsToPlot = years
    if "2016" in years and "2017" in years and "2018" in years:
        yearsToPlot.append("RunII")

    for y in yearsToPlot:
            
        JCMName="Nominal"
        FvTName="_Nominal"

        #histName3b = "hists_3b_wJCM_"+JCMName+"_wFVT"+FvTName+".root "
        #histName4b = "hists_4b_wFVT"+FvTName+".root "

        histName3b = "hists_3b_wJCM_"+JCMName+"_wFVT"+FvTName+"_"+tagID+".root "
        histName4b = "hists_4b_wFVT"+FvTName+"_"+tagID+".root "


        data3bFile  = getOutDir()+"/data"+y+"_"+tagID+"_3b_wFvT/"+histName3b    if not y == "RunII" else outputDir+"/data"+y+"/"+histName3b               
        data4bFile  = getOutDir()+"/data"+y+"_"+tagID+"_4b_wFvT/"+histName4b    if not y == "RunII" else outputDir+"/data"+y+"/"+histName4b               
        ttbar4bFile = getOutDir()+"/TT"+y+"/"+histName4b
        ttbar3bFile = getOutDir()+"/TT"+y+"/"+histName3b

        
        #cmd = "python ZZ4b/nTupleAnalysis/scripts/makeCutFlow.py "
        #cmd += " --d4 "+outputDir+"/data"+y+"/"+histName4b
        #cmd += " --d3 "+outputDirComb+"/data"+y+"/"+histName3b
        #cmd += " --t4 "+outputDir+"/TT"+y+"/"+histName4b
        #cmd += " --t3 "+outputDir+"/TT"+y+"/"+histName3b
        #cmd += " --t4_s "+outputDir+"/TTToSemiLeptonic"+y+"/"+histName4b
        #cmd += " --t4_h "+outputDir+"/TTToHadronic"+y+"/"+histName4b
        #cmd += " --t4_d "+outputDir+"/TTTo2L2Nu"+y+"/"+histName4b
        #cmd += " --t3_s "+outputDirComb+"/TTToSemiLeptonic"+y+"/"+histName3b
        #cmd += " --t3_h "+outputDirComb+"/TTToHadronic"+y+"/"+histName3b
        #cmd += " --t3_d "+outputDirComb+"/TTTo2L2Nu"+y+"/"+histName3b
        #cmd += " --name "+outputDir+"/CutFlow_wFvT_"+y
        #cmd += " --makePDF -r"
        #cmds.append(cmd)
        #logs.append(outputDir+"/log_cutFlow_wFVT_"+y)

        cmd = "python ZZ4b/nTupleAnalysis/scripts/makeCutFlow.py "
        cmd += " --d4 "+data4bFile
        cmd += " --d3 "+data3bFile
        cmd += " --t4 "+ttbar4bFile
        cmd += " --t3 "+ttbar3bFile
        cmd += " --name "+outputDir+"/CutFlow_wFvT_"+y+"_"+tagID
        cmd += " --makePDF -r"
        cmds.append(cmd)
        logs.append(outputDir+"/log_cutFlow_wFVT_"+y+"_"+tagID)


        cmd = "python ZZ4b/nTupleAnalysis/scripts/makePlots.py -o "+outputDir+" -p plotsWithFvT_"+y+"_"+tagID +plotOpts[y]+" -m -j -r --noSignal "
        cmd += " --data3b "+data3bFile
        cmd += " --data "+data4bFile
        cmd += " --TT "+ttbar4bFile
        cmds.append(cmd)
        logs.append(outputDir+"/log_makePlots_wFVT_"+y+"_"+tagID)


    babySit(cmds, doRun, logFiles=logs)    

    cmds = []
    for y in years:
        cmds.append("mv CutFlow_wFvT_"+y+"_"+tagID+".pdf "+outputDir+"/")
        cmds.append("tar -C "+outputDir+" -zcf "+outputDir+"/plotsWithFvT_"+y+"_"+tagID+".tar plotsWithFvT_"+y+"_"+tagID)
        
    babySit(cmds, doRun)    







#
#  Make Hists with JCM and FvT weights applied
#
if o.histsWithNoFvT:

    #
    #  Make Hists
    #
    cmds = []
    logs = []

    JCMName="Nominal"
    FvTName="_Nominal"

    histName3b = "hists_3b_wJCM_"+JCMName+"_noFvT_"+tagID+".root "
    histName4b = "hists_4b_noFvT_"+tagID+".root "

    for y in years:

        pico3b = "picoAOD_3b_wJCM_"+tagID+".root"
        picoOut = " -p NONE "
        h10 = " --histogramming 10 --histDetail 7 "    
        histOut3b = " --histFile "+histName3b

        cmds.append(runCMD+" -i "+outputDirComb+"/data"+y+"_"+tagID+"/"+pico3b+             picoOut  +   yearOpts[y]+ h10 + histOut3b + " --jcmNameLoad "+JCMName + " --FvTName "+FvTName)    
        logs.append(outputDir+"/log_"+y+"_3b_wJCM_noFVT_"+tagID)

        for tt in ttbarSamples:
            cmds.append(runCMD+" -i "+outputDirComb+"/"+tt+y+"_"+tagID+"/"+pico3b+     picoOut  + MCyearOpts[y]+ h10 + histOut3b + " --jcmNameLoad "+JCMName+ " --FvTName "+FvTName)    
            logs.append(outputDir+"/log_"+tt+y+"_3b_noJCM_noFVT_"+tagID)


        pico4b = "picoAOD_4b_"+tagID+".root"
        histOut4b = " --histFile "+histName4b

        cmds.append(runCMD+" -i "+outputDirComb+"/data"+y+"_"+tagID+"/"+pico4b+             picoOut  +   yearOpts[y]+ h10 + histOut4b + " --FvTName "+FvTName)     
        logs.append(outputDir+"/log_"+y+"_4b_noFVT_"+tagID)

        for tt in ttbarSamples:
            cmds.append(runCMD+" -i "+outputDirComb+"/"+tt+y+"_"+tagID+"/"+pico4b+     picoOut  + MCyearOpts[y]+ h10 + histOut4b + " --FvTName "+FvTName)     
            logs.append(outputDir+"/log_"+tt+y+"_4b_noFVT_"+tagID)

        
    babySit(cmds, doRun, logFiles=logs)

    
    #
    #  Hadd TTbar
    #
    cmds = []
    logs = []
    for y in years:
        cmds.append("hadd -f "+outputDir+"/TT"+y+"/"+histName3b+" "+outputDirComb+"/TTToHadronic"+y+"_"+tagID+"/"+histName3b+"  "+outputDirComb+"/TTToSemiLeptonic"+y+"_"+tagID+"/"+histName3b+" "+outputDirComb+"/TTTo2L2Nu"+y+"_"+tagID+"/"+histName3b)
        logs.append(outputDir+"/log_haddTT_3b_wJCM_noFvT_"+y+"_"+tagID)

        cmds.append("hadd -f "+outputDir+"/TT"+y+"/"+histName4b+" "+outputDirComb+"/TTToHadronic"+y+"_"+tagID+"/"+histName4b+"  "+outputDirComb+"/TTToSemiLeptonic"+y+"_"+tagID+"/"+histName4b+" "+outputDirComb+"/TTTo2L2Nu"+y+"_"+tagID+"/"+histName4b)
        logs.append(outputDir+"/log_haddTT_4b_noFvT_"+y+"_"+tagID)

    babySit(cmds, doRun, logFiles=logs)

    #
    # Subtract QCD 
    #
    cmds = []
    for y in years:
        mkdir(outputDir+"/QCD"+y, doRun)

        cmd = "python ZZ4b/nTupleAnalysis/scripts/subtractTT.py "
        cmd += " -d "+outputDirComb+"/data"+y+"_"+tagID+"/"+histName3b
        cmd += " --tt "+outputDir+"/TT"+y+"/"+histName3b
        cmd += " -q "+outputDir+"/QCD"+y+"/"+histName3b
        cmds.append(cmd)
        
    babySit(cmds, doRun)    



    #
    #   Hadd years
    #
    if "2016" in years and "2017" in years and "2018" in years:
    
        mkdir(outputDir+"/dataRunII", doRun)
        mkdir(outputDir+"/TTRunII",   doRun)
        mkdir(outputDir+"/QCDRunII",   doRun)

        cmds = []
        logs = []
        
        cmds.append("hadd -f "+outputDir+"/dataRunII/"+histName3b+" "+outputDirComb+"/data2016_"+tagID+"/"+histName3b+" "+outputDirComb+"/data2017_"+tagID+"/"+histName3b+" "+outputDirComb+"/data2018_"+tagID+"/"+histName3b)
        cmds.append("hadd -f "+outputDir+"/dataRunII/"+histName4b+" "+outputDirComb+"/data2016_"+tagID+"/"+histName4b+" "+outputDirComb+"/data2017_"+tagID+"/"+histName4b+" "+outputDirComb+"/data2018_"+tagID+"/"+histName4b)
        cmds.append("hadd -f "+outputDir+"/TTRunII/"  +histName4b+" "+outputDir+"/TT2016/"  +histName4b+" "+outputDir+"/TT2017/"  +histName4b+" "+outputDir+"/TT2018/"  +histName4b)
        cmds.append("hadd -f "+outputDir+"/TTRunII/"  +histName3b+" "+outputDir+"/TT2016/"  +histName3b+" "+outputDir+"/TT2017/"  +histName3b+" "+outputDir+"/TT2018/"  +histName3b)
        cmds.append("hadd -f "+outputDir+"/QCDRunII/"  +histName3b+" "+outputDir+"/QCD2016/"  +histName3b+" "+outputDir+"/QCD2017/"  +histName3b+" "+outputDir+"/QCD2018/"  +histName3b)

        logs.append(outputDir+"/log_haddDataRunII_3b_"+tagID+"_noFvT")
        logs.append(outputDir+"/log_haddDataRunII_4b_"+tagID+"_noFvT")
        logs.append(outputDir+"/log_haddDataRunII_TT_"+tagID+"_noFvT")
        logs.append(outputDir+"/log_haddDataRunII_TT_3b_"+tagID+"_noFvT")
        logs.append(outputDir+"/log_haddDataRunII_QCD_3b_"+tagID+"_noFvT")

        babySit(cmds, doRun, logFiles=logs)


    if o.email: execute('echo "Subject: [makeClosureNominal] histsWithNoFvT Done" | sendmail '+o.email,doRun)




#
#  Make CutFlows
#
if o.plotsWithNoFvT:
    cmds = []
    logs = []
    
    yearsToPlot = years
    if "2016" in years and "2017" in years and "2018" in years:
        yearsToPlot.append("RunII")

    for y in yearsToPlot:
            
        JCMName="Nominal"
        FvTName="_Nominal"


        histName3b = "hists_3b_wJCM_"+JCMName+"_noFvT_"+tagID+".root "
        histName4b = "hists_4b_noFvT_"+tagID+".root "

        qcdFile     = outputDir+"/QCD"+y+"/"+histName3b
        data3bFile  = outputDirComb+"/data"+y+"_"+tagID+"/"+histName3b    if not y == "RunII" else outputDir+"/data"+y+"/"+histName3b               
        data4bFile  = outputDirComb+"/data"+y+"_"+tagID+"/"+histName4b    if not y == "RunII" else outputDir+"/data"+y+"/"+histName4b               
        ttbar4bFile = outputDir+"/TT"+y+"/"+histName4b
        ttbar3bFile = outputDir+"/TT"+y+"/"+histName3b

        cmd = "python ZZ4b/nTupleAnalysis/scripts/makeCutFlow.py "
        cmd += " --d4 "+data4bFile
        cmd += " --d3 "+data3bFile
        cmd += " --t4 "+ttbar4bFile
        cmd += " --t3 "+ttbar3bFile
        cmd += " --name "+outputDir+"/CutFlow_noFvT_"+y+"_"+tagID
        cmd += " --makePDF "
        cmds.append(cmd)
        logs.append(outputDir+"/log_cutFlow_noFVT_"+y+"_"+tagID)


        cmd = "python ZZ4b/nTupleAnalysis/scripts/makePlots.py -o "+outputDir+" -p plotsWithNoFvT_"+y+"_"+tagID +plotOpts[y]+" -m -j  --noSignal "
        cmd += " --qcd "+qcdFile
        cmd += " --data "+data4bFile
        cmd += " --TT "+ttbar4bFile
        cmds.append(cmd)
        logs.append(outputDir+"/log_makePlots_noFVT_"+y+"_"+tagID)


    babySit(cmds, doRun, logFiles=logs)    

    cmds = []
    for y in years:
        cmds.append("mv CutFlow_noFvT_"+y+"_"+tagID+".pdf "+outputDir+"/")
        cmds.append("tar -C "+outputDir+" -zcf "+outputDir+"/plotsWithNoFvT_"+y+"_"+tagID+".tar plotsWithNoFvT_"+y+"_"+tagID)
        
    babySit(cmds, doRun)    







#
#  Make Hists with JCM and FvT weights applied
#
if o.moveFinalPicoAODsToEOS: 

    def copy(fileName, subDir, outFileName):
        cmd  = "xrdcp  "+fileName+" root://cmseos.fnal.gov//store/user/johnda/closureTest/results/3bAnd4b_b0p6/"+subDir+"/"+outFileName
    
        if doRun:
            os.system(cmd)
        else:
            print cmd



    for y in years:
        for sample in ["data","TTTo2L2Nu","TTToHadronic","TTToSemiLeptonic"]:

            subDir = sample+y #if tt == "data" else tt+y+"_noMjj"
            
            #
            # 3b 
            #
            pico3b = "picoAOD_3b_wJCM_b0p6.root"
            copy(outputDirComb+"/"+subDir+"_b0p6/"+pico3b, subDir,pico3b)

            #
            # 4b
            #
            pico4b = "picoAOD_4b_b0p6.root"
            copy(outputDirComb+"/"+subDir+"_b0p6/"+pico4b, subDir,pico4b)

        


#
#  Make Hists with JCM and FvT weights applied
#
if o.cleanFinalPicoAODsToEOS: 

    def rm(fileName):
        cmd  = "rm  "+fileName
    
        if doRun: os.system(cmd)
        else:     print cmd



    for y in years:
        for sample in ["data","TTTo2L2Nu","TTToHadronic","TTToSemiLeptonic"]:

            subDir = sample+y #if tt == "data" else tt+y+"_noMjj"
            
            #
            # 3b 
            #
            pico3b = "picoAOD_3b_wJCM_b0p6.root"
            rm(outputDirComb+"/"+subDir+"_b0p6/"+pico3b)

            #
            # 4b
            #
            pico4b = "picoAOD_4b_b0p6.root"
            rm(outputDirComb+"/"+subDir+"_b0p6/"+pico4b)

        
