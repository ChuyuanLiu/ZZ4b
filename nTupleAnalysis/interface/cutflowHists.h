// -*- C++ -*-
#if !defined(cutflowHists_H)
#define cutflowHists_H

#include <iostream>
#include <TH1F.h>
#include <TH2F.h>
#include "PhysicsTools/FWLite/interface/TFileService.h"
#include "ZZ4b/nTupleAnalysis/interface/eventData.h"

namespace nTupleAnalysis {

  class cutflowHists {
  public:
    TFileDirectory dir;
    
    TH1I* unitWeight;
    TH1D* weighted;

    TH2F* truthM4b = NULL;

    cutflowHists(std::string, fwlite::TFileService&, bool);
    void BasicFill(const std::string&, eventData*);
    void BasicFill(const std::string&, eventData*, float weight);
    void Fill(const std::string&, eventData*);

    void labelsDeflate();

    void AddCut(std::string cut);
    
    ~cutflowHists(); 

  };

}
#endif // cutflowHists_H
