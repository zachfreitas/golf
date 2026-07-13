"""Scatter charts for Zach's iron fit, in the dimensions that matter for HIM.

Chart 1  CG Map        : Effective VCOG (launch) vs RCOG (CG depth), bubble = MOI
Chart 2  Green-holding : robot Spin vs Descent angle (his deficit)
Chart 3  His two needs : robot Spin vs MOI (forgiveness)

Each highlights his gamer (P770) and all-time favorite (X-20 Tour) and shades the
"target zone". Colorblind-safe categorical palette (validated dataviz default).

Outputs: outputs/charts/*.png
"""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "irons_research"
OUT = ROOT / "outputs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

# --- validated palette (light mode) ---
SURFACE="#fcfcfb"; INK="#0b0b0b"; INK2="#52514e"; MUTED="#898781"; GRID="#e1e0d9"
CAT={"Players":"#2a78d6","Players Distance":"#1baf7a","Game Improvement":"#eda100",
     "Super Game Improvement":"#eb6834","Classic":"#4a3aa7","Conventional":"#898781"}
YOU="#e34948"; FAV="#4a3aa7"      # your gamer (red), your favorite (violet)

plt.rcParams.update({"figure.facecolor":SURFACE,"axes.facecolor":SURFACE,
    "font.family":"DejaVu Sans","text.color":INK,"axes.labelcolor":INK2,
    "xtick.color":MUTED,"ytick.color":MUTED,"axes.edgecolor":"#c3c2b7"})


def na(s): return re.sub(r"[^a-z0-9]","",str(s).lower())


def style(ax, title, sub, xlab, ylab):
    ax.set_title(title, fontsize=14, fontweight="bold", color=INK, pad=34, loc="left")
    ax.text(0,1.02, sub, transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")
    ax.set_xlabel(xlab, fontsize=10.5); ax.set_ylabel(ylab, fontsize=10.5)
    ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top","right"): ax.spines[s].set_visible(False)


def label(ax, x, y, txt, color=INK, dx=0, dy=8):
    ax.annotate(txt,(x,y),textcoords="offset points",xytext=(dx,dy),ha="center",
                fontsize=8.2, color=color, fontweight="bold")


# ================= Chart 1: CG map =================
def cg_map():
    s = pd.read_csv(D/"maltby_mpf_brand_specs.csv")
    for c in ("vcog_eff","rcog","moi","year"): s[c]=pd.to_numeric(s[c],errors="coerce")
    cur = s[(s.year>=2024) & s.vcog_eff.notna() & s.rcog.notna() & s.moi.notna()].copy()
    favs = s[((s.brand=="CALLAWAY")&s.model.str.contains("X-20 Tour|X-22 Tour",na=False)) |
             ((s.brand=="TAYLORMADE")&s.model.str.contains("P770 Forged",na=False)&(s.year==2023))].copy()
    fig,ax=plt.subplots(figsize=(10,7.5))
    # context: all current as light dots
    ax.scatter(cur.vcog_eff,cur.rcog,s=(cur.moi-10)*22,c="#d9d8d2",alpha=0.7,edgecolor="none",zorder=1)
    # shortlist highlights
    picks={"i240":"Ping i240","qi4dmaxhl":"TM Qi4D Max HL","staffdynapwr":"Wilson Staff Dynapwr",
           "apextifusion":"Apex Ti Fusion","p790#6":"P790","i540":"Ping i540",
           "ts35forged":"Maltby TS3.5","ts3dbmblack":"Maltby TS3 DBM"}
    for _,r in cur.iterrows():
        key=na(r.model)
        for tok,nm in picks.items():
            if tok in key:
                col=CAT.get(r.category,MUTED)
                ax.scatter(r.vcog_eff,r.rcog,s=(r.moi-10)*22,c=col,edgecolor="white",lw=1.2,zorder=3)
                label(ax,r.vcog_eff,r.rcog,nm,col); break
    # his clubs (each highlighted distinctly)
    X22="#e87ba4"  # magenta, distinct from X-20's violet
    for _,r in favs.iterrows():
        if r.brand=="TAYLORMADE":
            col,nm,mk,sz=YOU,"YOU: P770 (gamer)","D",170
        elif "X-20" in r.model:
            col,nm,mk,sz=FAV,"X-20 Tour (#1 fav)","*",440
        else:
            col,nm,mk,sz=X22,"X-22 Tour (#3 fav)","*",440
        ax.scatter(r.vcog_eff,r.rcog,s=sz,marker=mk,c=col,edgecolor="white",lw=1.4,zorder=5)
        label(ax,r.vcog_eff,r.rcog,nm,col,dy=11)
    # target zone: low effVCOG (<=0.72) + deep CG (rcog>=0.55)
    ax.axvspan(cur.vcog_eff.min()-0.01,0.72,ymin=0,ymax=1,color="#1baf7a",alpha=0.05,zorder=0)
    ax.axhline(0.55,color="#1baf7a",lw=1,ls="--",alpha=0.5,zorder=0)
    ax.axvline(0.72,color="#1baf7a",lw=1,ls="--",alpha=0.5,zorder=0)
    ax.invert_xaxis()  # lower effVCOG (higher launch) to the RIGHT
    style(ax,"Iron CG Map — launch vs forgiveness",
          "Bubble size = MOI (bigger = more forgiving). Target = lower CG + deeper CG (green zone, upper-right).",
          "← higher CG (lower launch)      Effective VCOG      lower CG (higher launch) →",
          "RCOG  —  CG depth (deeper / more launch + MOI →)")
    leg=[Line2D([0],[0],marker="D",color="w",markerfacecolor=YOU,markersize=10,label="Your P770 (gamer)"),
         Line2D([0],[0],marker="*",color="w",markerfacecolor=FAV,markersize=15,label="X-20 Tour (#1 favorite)"),
         Line2D([0],[0],marker="*",color="w",markerfacecolor="#e87ba4",markersize=15,label="X-22 Tour (#3 favorite)"),
         Line2D([0],[0],marker="o",color="w",markerfacecolor="#d9d8d2",markersize=10,label="Other 2024+ irons")]
    ax.legend(handles=leg,loc="lower left",frameon=False,fontsize=9)
    fig.tight_layout(); fig.savefig(OUT/"1_cg_map.png",dpi=150); plt.close(fig)
    print("wrote outputs/charts/1_cg_map.png")


# ================= Chart 2: green-holding =================
def green_holding():
    gd=pd.read_csv(D/"golfdigest_robot_2026.csv")
    fig,ax=plt.subplots(figsize=(10,7.5))
    for cat,g in gd.groupby("category"):
        ax.scatter(g.spin_rpm,g.descent_deg,s=90,c=CAT.get(cat,MUTED),edgecolor="white",
                   lw=1,label=cat,zorder=3,alpha=0.9)
    hi={"i240","Qi4D Max HL","Staff Dynapwr","P790","i540","0311P Gen 8","Apex Ti Fusion"}
    for _,r in gd.iterrows():
        if r.model in hi:
            label(ax,r.spin_rpm,r.descent_deg,f"{r.brand.title()} {r.model}",INK2,dy=8)
    # his P770 (GC3 @75mph)
    ax.scatter(4949,39.5,s=300,marker="D",c=YOU,edgecolor="white",lw=1.5,zorder=5)
    label(ax,4949,39.5,"YOU: P770 (GC3, 75mph)",YOU,dy=-16)
    # target zone: high spin + steep descent (upper right)
    ax.axvspan(5500,gd.spin_rpm.max()+150,color="#1baf7a",alpha=0.05)
    ax.axhline(45,color="#1baf7a",lw=1,ls="--",alpha=0.5)
    style(ax,"Green-holding — spin vs descent angle (robot, 7i @82mph)",
          "Your deficit is low spin + shallow descent. Target = upper-right (more spin, steeper landing).",
          "Backspin (rpm)  →  more spin","Descent angle (deg)  →  steeper / holds greens")
    ax.legend(loc="lower right",frameon=False,fontsize=9,title="Category")
    fig.tight_layout(); fig.savefig(OUT/"2_green_holding.png",dpi=150); plt.close(fig)
    print("wrote outputs/charts/2_green_holding.png")


# ================= Chart 3: spin vs MOI =================
def spin_vs_moi():
    gd=pd.read_csv(D/"golfdigest_robot_2026.csv")
    s=pd.read_csv(D/"maltby_mpf_brand_specs.csv"); s["moi"]=pd.to_numeric(s.moi,errors="coerce")
    s["year"]=pd.to_numeric(s.year,errors="coerce")
    def moi_for(b,m):
        sub=s[(s.brand.map(na)==na(b))&(s.year>=2024)]
        for _,r in sub.iterrows():
            if na(m)[:5] and (na(m)[:5] in na(r.model) or na(r.model)[:5] in na(m)): return r.moi
        return None
    gd["MOI"]=[moi_for(b,m) for b,m in zip(gd.brand,gd.model)]
    g=gd[gd.MOI.notna()]
    fig,ax=plt.subplots(figsize=(10,7.5))
    for cat,gg in g.groupby("category"):
        ax.scatter(gg.spin_rpm,gg.MOI,s=95,c=CAT.get(cat,MUTED),edgecolor="white",lw=1,label=cat,zorder=3)
    for _,r in g.iterrows():
        if r.model in {"i240","Qi4D Max HL","Staff Dynapwr","P790","i540","0311P Gen 8","Apex Ti Fusion","G740"}:
            label(ax,r.spin_rpm,r.MOI,f"{r.brand.title()} {r.model}",INK2,dy=8)
    ax.scatter(4949,11.54,s=300,marker="D",c=YOU,edgecolor="white",lw=1.5,zorder=5)
    label(ax,4949,11.54,"YOU: P770",YOU,dy=-16)
    ax.axvspan(5500,g.spin_rpm.max()+150,color="#1baf7a",alpha=0.05)
    ax.axhline(14,color="#1baf7a",lw=1,ls="--",alpha=0.5)
    style(ax,"Your two needs — spin vs forgiveness (MOI)",
          "You want BOTH: more spin (green-holding) and higher MOI (forgiveness). Sweet spot = upper-right.",
          "Backspin (rpm, robot 7i)  →  more spin","MOI (Maltby)  →  more forgiving")
    ax.legend(loc="upper left",frameon=False,fontsize=9,title="Category")
    fig.tight_layout(); fig.savefig(OUT/"3_spin_vs_moi.png",dpi=150); plt.close(fig)
    print("wrote outputs/charts/3_spin_vs_moi.png")


# ================= Chart 4: actual VCOG vs MOI =================
def actual_vcog_vs_moi():
    s = pd.read_csv(D/"maltby_mpf_brand_specs.csv")
    for c in ("vcog","moi","year"): s[c]=pd.to_numeric(s[c],errors="coerce")
    cur = s[(s.year>=2024) & s.vcog.notna() & s.moi.notna()].copy()
    favs = s[((s.brand=="CALLAWAY")&s.model.str.contains("X-20 Tour|X-22 Tour",na=False)) |
             ((s.brand=="TAYLORMADE")&s.model.str.contains("P770 Forged",na=False)&(s.year==2023))].copy()
    fig,ax=plt.subplots(figsize=(10,7.5))
    ax.scatter(cur.vcog,cur.moi,s=46,c="#d9d8d2",alpha=0.75,edgecolor="none",zorder=1)
    picks={"i240":"Ping i240","qi4dmaxhl":"TM Qi4D Max HL","staffdynapwr":"Wilson Staff Dynapwr",
           "apextifusion":"Apex Ti Fusion","p790#6":"P790","i540":"Ping i540",
           "ts35forged":"Maltby TS3.5","ts3dbmblack":"Maltby TS3 DBM","g740":"Ping G740"}
    for _,r in cur.iterrows():
        key=na(r.model)
        for tok,nm in picks.items():
            if tok in key:
                col=CAT.get(r.category,MUTED)
                ax.scatter(r.vcog,r.moi,s=95,c=col,edgecolor="white",lw=1.2,zorder=3)
                label(ax,r.vcog,r.moi,nm,col); break
    X22="#e87ba4"
    for _,r in favs.iterrows():
        if r.brand=="TAYLORMADE": col,nm,mk,sz=YOU,"YOU: P770 (gamer)","D",170
        elif "X-20" in r.model: col,nm,mk,sz=FAV,"X-20 Tour (#1 fav)","*",440
        else: col,nm,mk,sz=X22,"X-22 Tour (#3 fav)","*",440
        ax.scatter(r.vcog,r.moi,s=sz,marker=mk,c=col,edgecolor="white",lw=1.4,zorder=5)
        label(ax,r.vcog,r.moi,nm,col,dy=11)
    # target zone: lower actual CG + higher MOI (upper-right after x-invert)
    ax.axvspan(cur.vcog.min()-0.005,0.78,color="#1baf7a",alpha=0.05,zorder=0)
    ax.axhline(13.5,color="#1baf7a",lw=1,ls="--",alpha=0.5,zorder=0)
    ax.axvline(0.78,color="#1baf7a",lw=1,ls="--",alpha=0.5,zorder=0)
    ax.invert_xaxis()  # lower actual VCOG (higher launch) to the RIGHT
    style(ax,"Actual (Basic) VCOG vs MOI",
          "Actual measured CG height vs forgiveness. Note: basic VCOG ignores loft — read with the CG map.",
          "← higher CG (lower launch)     Actual VCOG (in)     lower CG (higher launch) →",
          "MOI  →  more forgiving")
    leg=[Line2D([0],[0],marker="D",color="w",markerfacecolor=YOU,markersize=10,label="Your P770 (gamer)"),
         Line2D([0],[0],marker="*",color="w",markerfacecolor=FAV,markersize=15,label="X-20 Tour (#1 favorite)"),
         Line2D([0],[0],marker="*",color="w",markerfacecolor="#e87ba4",markersize=15,label="X-22 Tour (#3 favorite)"),
         Line2D([0],[0],marker="o",color="w",markerfacecolor="#d9d8d2",markersize=10,label="Other 2024+ irons")]
    ax.legend(handles=leg,loc="lower left",frameon=False,fontsize=9)
    fig.tight_layout(); fig.savefig(OUT/"4_actual_vcog_vs_moi.png",dpi=150); plt.close(fig)
    print("wrote outputs/charts/4_actual_vcog_vs_moi.png")


# ================= Chart 5: effective VCOG vs MOI =================
def eff_vcog_vs_moi():
    s = pd.read_csv(D/"maltby_mpf_brand_specs.csv")
    for c in ("vcog_eff","moi","year"): s[c]=pd.to_numeric(s[c],errors="coerce")
    cur = s[(s.year>=2024) & s.vcog_eff.notna() & s.moi.notna()].copy()
    favs = s[((s.brand=="CALLAWAY")&s.model.str.contains("X-20 Tour|X-22 Tour",na=False)) |
             ((s.brand=="TAYLORMADE")&s.model.str.contains("P770 Forged",na=False)&(s.year==2023))].copy()
    fig,ax=plt.subplots(figsize=(10,7.5))
    ax.scatter(cur.vcog_eff,cur.moi,s=46,c="#d9d8d2",alpha=0.75,edgecolor="none",zorder=1)
    picks={"i240":"Ping i240","qi4dmaxhl":"TM Qi4D Max HL","staffdynapwr":"Wilson Staff Dynapwr",
           "apextifusion":"Apex Ti Fusion","p790#6":"P790","i540":"Ping i540",
           "ts35forged":"Maltby TS3.5","ts3dbmblack":"Maltby TS3 DBM","g740":"Ping G740"}
    for _,r in cur.iterrows():
        key=na(r.model)
        for tok,nm in picks.items():
            if tok in key:
                col=CAT.get(r.category,MUTED)
                ax.scatter(r.vcog_eff,r.moi,s=95,c=col,edgecolor="white",lw=1.2,zorder=3)
                label(ax,r.vcog_eff,r.moi,nm,col); break
    X22="#e87ba4"
    for _,r in favs.iterrows():
        if r.brand=="TAYLORMADE": col,nm,mk,sz=YOU,"YOU: P770 (gamer)","D",170
        elif "X-20" in r.model: col,nm,mk,sz=FAV,"X-20 Tour (#1 fav)","*",440
        else: col,nm,mk,sz=X22,"X-22 Tour (#3 fav)","*",440
        ax.scatter(r.vcog_eff,r.moi,s=sz,marker=mk,c=col,edgecolor="white",lw=1.4,zorder=5)
        label(ax,r.vcog_eff,r.moi,nm,col,dy=11)
    # target zone: low effVCOG (<=0.72, higher launch) + high MOI (>=13.5)
    ax.axvspan(cur.vcog_eff.min()-0.005,0.72,color="#1baf7a",alpha=0.05,zorder=0)
    ax.axhline(13.5,color="#1baf7a",lw=1,ls="--",alpha=0.5,zorder=0)
    ax.axvline(0.72,color="#1baf7a",lw=1,ls="--",alpha=0.5,zorder=0)
    ax.invert_xaxis()  # lower effective VCOG (higher launch) to the RIGHT
    style(ax,"Effective VCOG vs MOI — your two design levers",
          "Effective VCOG = Basic + Adjusted (loft-correct launch). Target = higher launch + higher MOI (green zone, upper-right).",
          "← higher CG (lower launch)   Effective VCOG   lower CG (higher launch) →",
          "MOI  →  more forgiving")
    leg=[Line2D([0],[0],marker="D",color="w",markerfacecolor=YOU,markersize=10,label="Your P770 (gamer)"),
         Line2D([0],[0],marker="*",color="w",markerfacecolor=FAV,markersize=15,label="X-20 Tour (#1 favorite)"),
         Line2D([0],[0],marker="*",color="w",markerfacecolor="#e87ba4",markersize=15,label="X-22 Tour (#3 favorite)"),
         Line2D([0],[0],marker="o",color="w",markerfacecolor="#d9d8d2",markersize=10,label="Other 2024+ irons")]
    ax.legend(handles=leg,loc="lower left",frameon=False,fontsize=9)
    fig.tight_layout(); fig.savefig(OUT/"5_eff_vcog_vs_moi.png",dpi=150); plt.close(fig)
    print("wrote outputs/charts/5_eff_vcog_vs_moi.png")


if __name__ == "__main__":
    cg_map(); green_holding(); spin_vs_moi(); actual_vcog_vs_moi(); eff_vcog_vs_moi()
