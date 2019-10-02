// -*- C++ -*-

#if !defined(eventData_H)
#define eventData_H

#include <iostream>
#include <TChain.h>
#include <TFile.h>
#include <TLorentzVector.h>
#include "nTupleAnalysis/baseClasses/interface/initBranch.h"
#include "nTupleAnalysis/baseClasses/interface/truthData.h"
#include "nTupleAnalysis/baseClasses/interface/jetData.h"
#include "nTupleAnalysis/baseClasses/interface/muonData.h"
#include "nTupleAnalysis/baseClasses/interface/dijet.h"
#include "nTupleAnalysis/baseClasses/interface/trijet.h"
#include "nTupleAnalysis/baseClasses/interface/trigData.h"
#include "ZZ4b/nTupleAnalysis/interface/eventView.h"
#include "TriggerEmulator/nTupleAnalysis/interface/TrigEmulatorTool.h"

// for jet pseudoTag calculations
#include <TRandom3.h>
#include <numeric> 
#include <boost/math/special_functions/binomial.hpp> 

namespace nTupleAnalysis {

  class eventData {

  public:
    // Member variables
    TChain* tree;
    bool isMC;
    std::string year;
    bool debug;
    bool printCurrentFile = false;
    bool fastSkim = false;
    UInt_t    run       =  0;
    UInt_t    lumiBlock =  0;
    ULong64_t event     =  0;
    Int_t     nPVs = 0;
    Int_t     nPVsGood = 0;
    Float_t   FvT = 0.5;
    Float_t   ZHvB = -99;
    Float_t   ZZvB = -99;
    Float_t   genWeight =  1;
    Float_t   weight    =  1;
    Float_t   weightNoTrigger    =  1;
    Float_t   trigWeight =  1;
    Float_t   mcWeight  =  1;
    Float_t   mcPseudoTagWeight = 1;
    Float_t   bTagSF = 1;
    int       nTrueBJets = 0;

    nTupleAnalysis::truthData* truth = NULL;

    //Predefine btag sorting functions
    float       bTag    = 0.8484;//medium WP for CSVv2 https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation80XReReco
    std::string bTagger = "CSVv2";
    bool (*sortTag)(std::shared_ptr<nTupleAnalysis::jet>&, std::shared_ptr<nTupleAnalysis::jet>&);

    //triggers
    bool passHLT             = false;
    bool passL1              = false;
    //2016
    bool HLT_4j45_3b087      = false;
    bool HLT_2j90_2j30_3b087 = false;
    //2017
    bool HLT_HT300_4j_75_60_45_40_3b = false;
    bool HLT_mu12_2j40_dEta1p6_db    = false;
    bool HLT_mu12_2j350_1b           = false;
    bool HLT_J400_m30                = false;
    //2018
    bool HLT_HT330_4j_75_60_45_40_3b = false;
    bool HLT_4j_103_88_75_15_2b_VBF1 = false;
    bool HLT_4j_103_88_75_15_1b_VBF2 = false;
    bool HLT_2j116_dEta1p6_2b        = false;
    bool HLT_J330_m30_2b             = false;
    bool HLT_j500                    = false; // also 2017
    bool HLT_2j300ave                = false;
    bool L1_HTT280er = false;
    bool L1_HTT360er = false;
    bool L1_ETT2000 = false;
    bool L1_HTT320er_QuadJet_70_55_40_40_er2p4 = false;


    //
    //  trigger Emulation
    //
    bool doTrigEmulation = false;
    TriggerEmulator::TrigEmulatorTool* trigEmulator;

    //
    //  Ht Turnon study
    //
    bool doHtTurnOnStudy = true;
    bool HLT_HT330_4j_75_60_45_40    = false;

    const float jetPtMin = 40;
    const float jetEtaMax= 2.4;
    const bool doJetCleaning=false;
     
    nTupleAnalysis::jetData* treeJets;
    std::vector< std::shared_ptr<nTupleAnalysis::jet> > allJets;//all jets in nTuple
    std::vector< std::shared_ptr<nTupleAnalysis::jet> > selJets;//jets passing pt/eta requirements
    std::vector< std::shared_ptr<nTupleAnalysis::jet> > tagJets;//jets passing pt/eta and bTagging requirements
    std::vector< std::shared_ptr<nTupleAnalysis::jet> > antiTag;//jets passing pt/eta and failing bTagging requirements
    std::vector< std::shared_ptr<nTupleAnalysis::jet> > canJets;//jets used in Z/H boson candidates
    std::vector< std::shared_ptr<nTupleAnalysis::jet> > othJets;//other selected jets
    std::vector< std::shared_ptr<nTupleAnalysis::trig> > allTrigJets;//all jets in nTuple
    float ht, ht30, L1ht, L1ht30, HLTht, HLTht30;
    std::vector< std::shared_ptr<nTupleAnalysis::jet> > allNotCanJets;//other jets pt>20
 
    uint nSelJets;
    uint nTagJets;
    uint nAntiTag;
    uint nPSTJets;
    uint nOthJets;
    uint nAllNotCanJets;
    bool threeTag;
    bool fourTag;

    float st;
    TLorentzVector p4j;//combined 4-vector of the candidate jet system
    float m4j;
    float m123; float m013; float m023; float m012;
    float s4j;
    float canJet0_pt ; float canJet1_pt ; float canJet2_pt ; float canJet3_pt ;
    float canJet0_eta; float canJet1_eta; float canJet2_eta; float canJet3_eta;
    float canJet0_phi; float canJet1_phi; float canJet2_phi; float canJet3_phi;
    float canJet0_m  ; float canJet1_m  ; float canJet2_m  ; float canJet3_m  ;
    float aveAbsEta; float aveAbsEtaOth; float stNotCan;
    float dRjjClose;
    float dRjjOther;
    float othJet_pt[40]; float othJet_eta[40]; float othJet_phi[40]; float othJet_m[40];
    float notCanJet_pt[40]; float notCanJet_eta[40]; float notCanJet_phi[40]; float notCanJet_m[40];
    
    bool ZHSB; bool ZHCR; bool ZHSR;
    bool ZZSB; bool ZZCR; bool ZZSR;
    bool SB; bool CR; bool SR;
    float leadStM; float sublStM;

    nTupleAnalysis::muonData* treeMuons;
    std::vector< std::shared_ptr<nTupleAnalysis::muon> > allMuons;
    std::vector< std::shared_ptr<nTupleAnalysis::muon> > isoMuons;

    std::vector< std::shared_ptr<nTupleAnalysis::dijet> > dijets;
    std::shared_ptr<nTupleAnalysis::dijet> close;
    std::shared_ptr<nTupleAnalysis::dijet> other;
    std::vector< std::unique_ptr<eventView> > views;
    bool passDijetMass;
    bool passMDRs;
    bool passXWt;
    bool passDEtaBB;


    nTupleAnalysis::trigData* treeTrig = NULL;

    // Constructors and member functions
    eventData(TChain*, bool, std::string, bool, bool _fastSkim = false, bool _doTrigEmulation = false); 
    void setTagger(std::string, float);
    void update(long int);
    void buildEvent();
    void resetEvent();

    // 
    //  Used to make new events with hemisphere mixing
    //
    int makeNewEvent(std::vector<nTupleAnalysis::jetPtr> new_allJets);

    //jet combinatorics
    bool useJetCombinatoricModel = false;
    float pseudoTagProb = -1;
    float pairEnhancement = 0.0;
    float pairEnhancementDecay = 1.0;
    float pseudoTagProb_lowSt = -1;
    float pairEnhancement_lowSt = 0.0;
    float pairEnhancementDecay_lowSt = 1.0;
    float pseudoTagProb_midSt = -1;
    float pairEnhancement_midSt = 0.0;
    float pairEnhancementDecay_midSt = 1.0;
    float pseudoTagProb_highSt = -1;
    float pairEnhancement_highSt = 0.0;
    float pairEnhancementDecay_highSt = 1.0;
    Float_t   pseudoTagWeight = 1;
    std::vector<float> nPseudoTagProb;
    uint nPseudoTags = 0;
    TRandom3* random;
    void computePseudoTagWeight();
    float FvTWeight = 1;

    void chooseCanJets();
    void buildViews();
    void applyMDRs();
    
    std::shared_ptr<nTupleAnalysis::trijet> t;
    std::shared_ptr<nTupleAnalysis::trijet> t0;
    std::shared_ptr<nTupleAnalysis::trijet> t1;
    //std::shared_ptr<nTupleAnalysis::trijet> t2;
    float xWt0; float xWt1; float xWt; //float xWt2;

    void buildTops();
    void dump();
    ~eventData(); 

    std::string currentFile = "";

  };

}
#endif // eventData_H
