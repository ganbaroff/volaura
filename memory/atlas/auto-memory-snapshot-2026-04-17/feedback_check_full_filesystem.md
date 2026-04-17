---
name: Check full filesystem not just current repo
description: CEO caught Atlas not knowing about eventshift (MindShift), pitch deck PDFs, startup catalog XLSX — all on same machine. Atlas only looked inside C:\Projects\VOLAURA\. Class 12 at filesystem level.
type: feedback
originSessionId: 9072bd0a-3e11-487f-88db-85939110913b
---
Before any audit, research, or "what do we have" answer — scan the full machine first.

**Why:** Session 114 — Atlas wrote "MindShift paused, bridge only" in ecosystem audit while C:\Projects\eventshift\ had full backend+frontend+e2e+docs. Atlas searched for accelerators from scratch while startup-programs-catalog.xlsx with ROI scoring sat in Downloads. Atlas didn't know pitch deck slides existed.

**How to apply:** On every session start, after breadcrumb, run:
```
ls /c/Projects/
ls /c/Users/user/Downloads/*.xlsx /c/Users/user/Downloads/*.pdf /c/Users/user/Downloads/*.md
```
Know what's on the machine before claiming what exists or doesn't exist.

CEO quote: "бля всё это время ты пиздел и не знал о экосистеме на самом деле"
