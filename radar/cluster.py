from __future__ import annotations
import re
def shingles(text: str, k: int=3) -> set[tuple[str,...]]:
    words=re.findall(r"\w+",text.casefold()); return set(zip(*(words[i:] for i in range(k)))) if len(words)>=k else {tuple(words)} if words else set()
def cluster_pains(pains: list[object], threshold: float=.35) -> list[tuple[str,...]]:
    parent=list(range(len(pains)))
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]];i=parent[i]
        return i
    def join(a,b): parent[find(a)]=find(b)
    terms=[shingles(f"{p.pain} {p.icp}") for p in pains]
    for i in range(len(pains)):
        for j in range(i):
            union=terms[i]|terms[j]
            if union and len(terms[i]&terms[j])/len(union)>=threshold: join(i,j)
    groups={}
    for i,p in enumerate(pains): groups.setdefault(find(i),[]).append(p.id)
    return [tuple(v) for _,v in sorted(groups.items(),key=lambda x:x[1])]
