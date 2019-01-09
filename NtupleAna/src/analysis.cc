#include <iostream>
#include <iomanip>
#include <TROOT.h>

#include "ZZ4b/NtupleAna/interface/analysis.h"

using namespace NtupleAna;

analysis::analysis(TChain* t, fwlite::TFileService& fs, bool d) {
  std::cout<<"In analysis constructor"<<std::endl;
  debug      = d;
  tree       = t;
  event      = new eventData(tree, debug);
  treeEvents = tree->GetEntries();
  cutflow    = new cutflowHists("cutflow", fs);

  // hists
  allEvents    = new eventHists("allEvents", fs);
    //     self.allEvents   = truthHists(self.outFile, "allEvents")
    //     self.passPreSel  = eventHists(self.outFile, "passPreSel",  True)
    //     self.passMDRs    = eventHists(self.outFile, "passMDRs",    True)
    //     self.passMDCs    = eventHists(self.outFile, "passMDCs",    True)
    //     self.passHCdEta  = eventHists(self.outFile, "passHCdEta",  True)
    //     self.passTopVeto = eventHists(self.outFile, "passTopVeto", True)

    //     #event
    //     self.thisEvent = eventData(self.tree, self.debug)
} 

int analysis::eventLoop(int maxEvents) {
  std::cout << " In eventLoop" << std::endl;
  nEvents = (maxEvents > 0 && maxEvents < treeEvents) ? maxEvents : treeEvents;

  // //
  // // Make output ntuple/Hists
  // // 

  // //EventHists eventHists     = EventHists("AllEvents", fs);
  
  std::cout << "Number of input events: " << treeEvents << std::endl;
  std::cout << "Will process " << nEvents << " events." << std::endl;

  for(int e = 0; e < nEvents; e++){

    event->update(e);
    processEvent();
    if(debug) event->dump();

    if( (e+1)%1000 == 0 || debug)
      std::cout << "Processed: "<<std::setw(8)<<e+1<<" of "<<nEvents<<" Events"<<std::endl;
  }

  std::cout<<"Exit eventLoop"<<std::endl;
  return 0;
}

int analysis::processEvent() {
  //     #initialize event and do truth level stuff before moving to reco (actual data analysis) stuff
  event->weight *= lumi/nEvents * kFactor;

  cutflow->Fill("all", event->weight);
  allEvents->Fill(event);

  //
  // Preselection
  // 
  bool jetMultiplicity = (event->selJets.size() >= 4);
  if(!jetMultiplicity){
    if(debug) std::cout << "Fail Jet Multiplicity" << std::endl;
    return 0;
  }
  cutflow->Fill("jetMultiplicity", event->weight);

  bool bTags = (event->tagJets.size() >= 4);
  if(!bTags){
    if(debug) std::cout << "Fail b-tag " << std::endl;
    return 0;
  }
  cutflow->Fill("bTags", event->weight);

    //     #
    //     #if event passes basic cuts start doing higher level constructions
    //     #
    //     self.thisEvent.buildViews(self.thisEvent.recoJets)
    //     self.thisEvent.buildTops(self.thisEvent.recoJets, [])
    //     self.passPreSel.Fill(self.thisEvent, self.thisEvent.weight)

    //     self.thisEvent.applyMDRs()
    //     if not self.thisEvent.views:
    //         if self.debug: print( "No Views Pass MDRs" )
    //         return
    //     self.cutflow.Fill("MDRs", self.thisEvent.weight)
    //     self.passMDRs.Fill(self.thisEvent, self.thisEvent.weight)

    //     if not self.thisEvent.views[0].passMDCs:
    //         if self.debug: print( "Fail MDCs" )
    //         return
    //     self.cutflow.Fill("MDCs", self.thisEvent.weight)
    //     self.passMDCs.Fill(self.thisEvent, self.thisEvent.weight)
        
    //     if not self.thisEvent.views[0].passHCdEta:
    //         if self.debug: print( "Fail HC dEta" )
    //         return
    //     self.cutflow.Fill("HCdEta", self.thisEvent.weight)
    //     self.passHCdEta.Fill(self.thisEvent, self.thisEvent.weight)
        
    //     if not self.thisEvent.passTopVeto:
    //         if self.debug: print( "Fail top veto" )
    //         return
    //     self.cutflow.Fill("topVeto", self.thisEvent.weight)
    //     self.passTopVeto.Fill(self.thisEvent, self.thisEvent.weight)
        
    //     if not self.thisEvent.views[0].ZZ:
    //         if self.debug: print( "Fail xZZ =",self.thisEvent.views[0].xZZ )
    //         return
    //     self.cutflow.Fill("xZZ", self.thisEvent.weight)
  return 0;
}

analysis::~analysis(){} 
