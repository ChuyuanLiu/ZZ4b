#include "ZZ4b/nTupleAnalysis/interface/tagHists.h"

using namespace nTupleAnalysis;

tagHists::tagHists(std::string name, fwlite::TFileService& fs, bool doViews, bool isMC, bool blind, int detailLevel, bool _debug, eventData* event) {
  std::cout << "Initialize >>   tagHists: " << name << " with detail level: " << detailLevel << std::endl;
  dir = fs.mkdir(name);
  debug = _debug;

  threeTag = new eventHists(name+"/threeTag", fs, doViews, isMC, false, detailLevel, debug, event);
  fourTag  = new eventHists(name+"/fourTag",  fs, doViews, isMC, blind, detailLevel, debug, event);

} 

void tagHists::Fill(eventData* event){

  if(event->threeTag) threeTag->Fill(event);
  if(event->fourTag)   fourTag->Fill(event);

  return;
}

void tagHists::Fill(eventData* event, std::vector<std::unique_ptr<eventView>> &views){

  if(event->threeTag) threeTag->Fill(event, views);
  if(event->fourTag)   fourTag->Fill(event, views);

  return;
}

tagHists::~tagHists(){} 


