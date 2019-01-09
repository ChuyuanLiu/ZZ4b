#include <iostream>

#include "ZZ4b/NtupleAna/interface/eventData.h"

using namespace NtupleAna;


eventData::eventData(TChain* t, bool d){
  tree  = t;
  debug = d;

  if(debug){
    std::cout<<"tree->Show(0)"<<std::endl;
    tree->Show(0);
  }

  tree->SetBranchAddress("run",       &run);
  tree->SetBranchAddress("event",     &event);
  tree->SetBranchAddress("genWeight", &weight);

  treeJets  = new jetData( "Jet",  tree);
  treeMuons = new muonData("Muon", tree);
} 


void eventData::update(int e){
  if(debug) std::cout<<"Get Entry "<<e<<std::endl;
  tree->GetEntry(e);

  allJets = treeJets->getJets();
  selJets = treeJets->getJets(40, 2.5);
  tagJets = treeJets->getJets(40, 2.5, 0.4941);//medium WP 2017 from AN2018_073_v10

  allMuons = treeMuons->getMuons();
  isoMuons = treeMuons->getMuons(40, 2.5, 1, true);
  //Hack to use leptons as bJets until we get real 4b samples
  for(auto muon: isoMuons){
    selJets.push_back(jet(muon.p, 1.0));
    tagJets.push_back(jet(muon.p, 1.0));
  }

  return;
}


void eventData::dump(){

  std::cout << "   Run: " << run    << std::endl;
  std::cout << " Event: " << event  << std::endl;  
  std::cout << "Weight: " << weight << std::endl;
  std::cout << " allJets: " << allJets .size() << " |  selJets: " << selJets .size() << " | tagJets: " << tagJets.size() << std::endl;
  std::cout << "allMuons: " << allMuons.size() << " | isoMuons: " << isoMuons.size() << std::endl;

  return;
}

eventData::~eventData(){} 

