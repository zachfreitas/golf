"""Scatter charts for Zach's iron fit, in the dimensions that matter for HIM.

Chart 1  CG Map        : Effective VCOG (launch) vs RCOG (CG depth), bubble = MOI
Chart 2  Green-holding : robot Spin vs Descent angle
Chart 3  Two needs     : robot Spin vs MOI (forgiveness)
Chart 4  Actual VCOG vs MOI
Chart 5  Effective VCOG vs MOI

Every club that falls in a chart's green TARGET zone is colored (by category) and
labeled by name; everything else is a light-gray context dot. His gamer (P770) and
favorites (X-20 / X-22 Tour) are always highlighted. Colorblind-safe palette.

Outputs: outputs/charts/*.png    (use --since YYYY to change the CG-chart year window)
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

YEAR_MIN = 2024  # CG charts (1,4,5) show irons with year >= this (--since to change; 0 = all)

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "irons_research"
OUT = ROOT / "outputs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

SURFACE="#fcfcfb"; INK="#0b0b0b"; INK2="#52514e"; MUTED="#898781"; GRID="#e1e0d9"
CAT={"Players":"#2a78d6","Players Distance":"#1baf7a","Game Improvement":"#eda100",
     "Super Game Improvement":"#eb6834","Classic":"#4a3aa7","Conventional":"#4a3aa7"}
YOU="#e34948"; FAV="#4a3aa7"; X22C="#e87ba4"; GREEN="#1baf7a"

plt.rcParams.update({"figure.facecolor":SURFACE,"axes.facecolor":SURFACE,
    "font.family":"DejaVu Sans","text.color":INK,"axes.labelcolor":INK2,
    "xtick.color":MUTED,"ytick.color":MUTED,"axes.edgecolor":"#c3c2b7"})


def na(s): return re.sub(r"[^a-z0-9]","",str(s).lower())
def clean(m): return re.sub(r"\s*#\s*\d+\b","",str(m)).strip()


def style(ax, title, sub, xlab, ylab):
    ax.set_title(title, fontsize=14, fontweight="bold", color=INK, pad=34, loc="left")
    ax.text(0,1.02, sub, transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")
    ax.set_xlabel(xlab, fontsize=10.5); ax.set_ylabel(ylab, fontsize=10.5)
    ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top","right"): ax.spines[s].set_visible(False)


def zone_rect(ax, x_thr, x_dir, y_thr, y_dir):
    """Shade the 2D target rectangle within the current data limits (call AFTER plotting).
    x_dir/y_dir: 'low' (<=thr good) or 'high' (>=thr good)."""
    x0,x1=sorted(ax.get_xlim()); y0,y1=sorted(ax.get_ylim())
    rx0,rx1=(x0,x_thr) if x_dir=="low" else (x_thr,x1)
    ry0,ry1=(y_thr,y1) if y_dir=="high" else (y0,y_thr)
    ax.add_patch(Rectangle((rx0,ry0),rx1-rx0,ry1-ry0,color=GREEN,alpha=0.08,zorder=0,lw=0))
    ax.axvline(x_thr,color=GREEN,lw=1,ls="--",alpha=0.55,zorder=0)
    ax.axhline(y_thr,color=GREEN,lw=1,ls="--",alpha=0.55,zorder=0)
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1)


def label_all(ax, df, xcol, ycol):
    """Color + label every row (used for the in-zone set). Stagger labels to reduce overlap."""
    rows=[r for _,r in df.iterrows()]
    rows.sort(key=lambda r:(r[xcol], r[ycol]))
    for i,r in enumerate(rows):
        col=CAT.get(r.get("category",""),MUTED)
        ax.scatter(r[xcol],r[ycol],s=80,c=col,edgecolor="white",lw=1.1,zorder=3)
        dy=10 if i%2==0 else -14
        ax.annotate(f"{str(r['brand']).title()} {clean(r['model'])}",(r[xcol],r[ycol]),
                    textcoords="offset points",xytext=(0,dy),ha="center",fontsize=7.6,
                    color=col,fontweight="bold",zorder=6)


def mark_you(ax, x, y, txt, color, sz=170, mk="D", dy=11):
    ax.scatter(x,y,s=sz,marker=mk,c=color,edgecolor="white",lw=1.4,zorder=7)
    ax.annotate(txt,(x,y),textcoords="offset points",xytext=(0,dy),ha="center",
                fontsize=8.4,color=color,fontweight="bold",zorder=8)


def you_legend():
    return [Line2D([0],[0],marker="D",color="w",markerfacecolor=YOU,markersize=10,label="Your P770 (gamer)"),
            Line2D([0],[0],marker="*",color="w",markerfacecolor=FAV,markersize=15,label="X-20 Tour (#1 favorite)"),
            Line2D([0],[0],marker="*",color="w",markerfacecolor=X22C,markersize=15,label="X-22 Tour (#3 favorite)"),
            Line2D([0],[0],marker="o",color="w",markerfacecolor=GREEN,markersize=10,label="In green zone (labeled)"),
            Line2D([0],[0],marker="o",color="w",markerfacecolor="#d9d8d2",markersize=9,label="Outside zone")]


def maltby_current():
    s=pd.read_csv(D/"maltby_mpf_brand_specs.csv")
    for c in ("vcog","vcog_eff","moi","rcog","year"): s[c]=pd.to_numeric(s[c],errors="coerce")
    cur=s[(s.year>=YEAR_MIN)].dropna(subset=["vcog","vcog_eff","moi","rcog"]).copy()
    favs=s[((s.brand=="CALLAWAY")&s.model.str.contains("X-20 Tour|X-22 Tour",na=False)) |
           ((s.brand=="TAYLORMADE")&s.model.str.contains("P770 Forged",na=False)&(s.year==2023))].copy()
    return cur,favs


# ---------- CG-based charts ----------
def _cg_chart(xcol, ycol, x_thr, x_dir, y_thr, y_dir, title, sub, xlab, ylab, fname, ylead=None):
    cur,favs=maltby_current()
    fig,ax=plt.subplots(figsize=(11,8))
    inzone=cur[_mask(cur,xcol,x_thr,x_dir) & _mask(cur,ycol,y_thr,y_dir)]
    out=cur.drop(inzone.index)
    ax.scatter(out[xcol],out[ycol],s=42,c="#d9d8d2",alpha=0.7,edgecolor="none",zorder=1)
    label_all(ax,inzone,xcol,ycol)
    # his clubs
    for _,r in favs.iterrows():
        yv=r[ycol]
        if r.brand=="TAYLORMADE": mark_you(ax,r[xcol],yv,"YOU: P770 (gamer)",YOU,170,"D")
        elif "X-20" in r.model: mark_you(ax,r[xcol],yv,"X-20 Tour (#1)",FAV,440,"*")
        else: mark_you(ax,r[xcol],yv,"X-22 Tour (#3)",X22C,440,"*")
    zone_rect(ax,x_thr,x_dir,y_thr,y_dir)
    if x_dir=="low": ax.invert_xaxis()
    style(ax,title,sub,xlab,ylab)
    ax.legend(handles=you_legend(),loc="lower left",frameon=False,fontsize=8.5)
    fig.tight_layout(); fig.savefig(OUT/fname,dpi=150); plt.close(fig)
    print(f"wrote outputs/charts/{fname}  ({len(inzone)} clubs in green zone)")


def _mask(df,col,thr,d): return df[col]<=thr if d=="low" else df[col]>=thr


def cg_map():
    _cg_chart("vcog_eff","rcog",0.72,"low",0.55,"high",
        "Iron CG Map — launch vs CG depth",
        "Green zone = lower CG (effVCOG <= 0.72) AND deeper CG (RCOG >= 0.55). All zone clubs labeled.",
        "<- higher CG (lower launch)     Effective VCOG     lower CG (higher launch) ->",
        "RCOG  —  CG depth (deeper / more launch + MOI ->)","1_cg_map.png")

def actual_vcog_vs_moi():
    _cg_chart("vcog","moi",0.78,"low",13.5,"high",
        "Actual (Basic) VCOG vs MOI",
        "Green zone = lower basic CG (VCOG <= 0.78) AND MOI >= 13.5. All zone clubs labeled.",
        "<- higher CG (lower launch)     Actual VCOG (in)     lower CG (higher launch) ->",
        "MOI  ->  more forgiving","4_actual_vcog_vs_moi.png")

def eff_vcog_vs_moi():
    _cg_chart("vcog_eff","moi",0.72,"low",13.5,"high",
        "Effective VCOG vs MOI — your two design levers",
        "Green zone = higher launch (effVCOG <= 0.72) AND MOI >= 13.5. All zone clubs labeled.",
        "<- higher CG (lower launch)     Effective VCOG     lower CG (higher launch) ->",
        "MOI  ->  more forgiving","5_eff_vcog_vs_moi.png")


# ---------- robot charts ----------
def _robot(ycol, y_thr, title, sub, ylab, fname, need_moi=False):
    gd=pd.read_csv(D/"golfdigest_robot_2026.csv")
    gd["spin_rpm"]=pd.to_numeric(gd.spin_rpm,errors="coerce")
    gd[ycol]=pd.to_numeric(gd[ycol],errors="coerce") if ycol in gd else None
    if need_moi:
        s=pd.read_csv(D/"maltby_mpf_brand_specs.csv"); s["moi"]=pd.to_numeric(s.moi,errors="coerce"); s["year"]=pd.to_numeric(s.year,errors="coerce")
        def moi_for(b,m):
            sub=s[(s.brand.map(na)==na(b))&(s.year>=2024)]
            for _,r in sub.iterrows():
                if na(m)[:5] and (na(m)[:5] in na(r.model) or na(r.model)[:5] in na(m)): return r.moi
            return None
        gd["MOI"]=[moi_for(b,m) for b,m in zip(gd.brand,gd.model)]; ycol="MOI"; gd=gd.dropna(subset=["MOI"])
    fig,ax=plt.subplots(figsize=(11,8))
    inzone=gd[(gd.spin_rpm>=5500)&(gd[ycol]>=y_thr)]
    out=gd.drop(inzone.index)
    ax.scatter(out.spin_rpm,out[ycol],s=48,c="#d9d8d2",alpha=0.75,edgecolor="none",zorder=1)
    label_all(ax,inzone,"spin_rpm",ycol)
    mark_you(ax,4949,(39.5 if ycol=="descent_deg" else 11.54),
             "YOU: P770 (GC3, 75mph)"+("" if ycol=="descent_deg" else " MOI"),YOU,300,"D",-16)
    zone_rect(ax,5500,"high",y_thr,"high")
    style(ax,title,sub,"Backspin (rpm, robot 7i @82mph)  ->  more spin",ylab)
    ax.legend(handles=you_legend()[:1]+you_legend()[3:],loc="lower right",frameon=False,fontsize=8.5)
    fig.tight_layout(); fig.savefig(OUT/fname,dpi=150); plt.close(fig)
    print(f"wrote outputs/charts/{fname}  ({len(inzone)} clubs in green zone)")


def green_holding():
    _robot("descent_deg",45.0,
        "Green-holding — spin vs descent angle (robot 7i @82mph)",
        "Green zone = spin >= 5,500 AND descent >= 45 deg. All zone clubs labeled.",
        "Descent angle (deg)  ->  steeper / holds greens","2_green_holding.png")

def spin_vs_moi():
    _robot("MOI",14.0,
        "Your two needs — spin vs forgiveness (MOI)",
        "Green zone = spin >= 5,500 AND MOI >= 14. All zone clubs labeled.",
        "MOI (Maltby)  ->  more forgiving","3_spin_vs_moi.png",need_moi=True)


# ---------- pooled multi-source robot charts (2b, 3b) ----------
SRC_MK={"GD":"o","CC":"^","MGS":"s"}   # marker shape per source
SRC_NAME={"GD":"Golf Digest (82mph)","CC":"Cool Clubs (80mph steel)","MGS":"MyGolfSpy"}


def _combined_robot():
    """Union of measured spin/descent from all three robot sources (67 models).
    Conditions differ by source (see SRC_NAME) -> compare within a source; the pooled
    view is for coverage. MOI is joined from Maltby specs (source-independent)."""
    gd=pd.read_csv(D/"golfdigest_robot_2026.csv").rename(columns={})
    gd=gd[["brand","model","spin_rpm","descent_deg","category"]].assign(src="GD")
    mgs=pd.read_csv(D/"mygolfspy_robot.csv").rename(columns={"oem":"brand","spin":"spin_rpm","descent":"descent_deg"})
    mgs=mgs[["brand","model","spin_rpm","descent_deg","category"]].assign(src="MGS")
    cc=pd.read_csv(D/"coolclubs_iron_data.csv")[["brand","model","spin_rpm","descent_deg"]].assign(src="CC",category="")
    df=pd.concat([gd,mgs,cc],ignore_index=True)
    for c in ("spin_rpm","descent_deg"): df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.dropna(subset=["spin_rpm"]).copy()
    # fill missing category (Cool Clubs) from any same-name row that has one
    catmap={}
    for _,r in df.iterrows():
        if r.category: catmap.setdefault(na(r.brand)+na(r.model)[:6], r.category)
    df["category"]=[c if c else catmap.get(na(b)+na(m)[:6],"") for b,m,c in zip(df.brand,df.model,df.category)]
    # MOI from Maltby specs
    s=pd.read_csv(D/"maltby_mpf_brand_specs.csv"); s["moi"]=pd.to_numeric(s.moi,errors="coerce"); s["year"]=pd.to_numeric(s.year,errors="coerce")
    def moi_for(b,m):
        sub=s[(s.brand.map(na)==na(b))&(s.year>=2023)]
        for _,r in sub.iterrows():
            if na(m)[:5] and (na(m)[:5] in na(r.model) or na(r.model)[:5] in na(m)): return r.moi
        return None
    df["moi"]=[moi_for(b,m) for b,m in zip(df.brand,df.model)]
    return df


def _pooled(ycol,y_thr,title,sub,ylab,fname,need_moi=False):
    df=_combined_robot()
    if need_moi: df=df.dropna(subset=["moi"]); ycol="moi"
    else: df=df.dropna(subset=[ycol])
    inzone=df[(df.spin_rpm>=5500)&(df[ycol]>=y_thr)]
    out=df.drop(inzone.index)
    fig,ax=plt.subplots(figsize=(12,8.5))
    for src,mk in SRC_MK.items():
        o=out[out.src==src]
        ax.scatter(o.spin_rpm,o[ycol],s=44,marker=mk,c="#d9d8d2",alpha=0.75,edgecolor="none",zorder=1)
    rows=sorted([r for _,r in inzone.iterrows()],key=lambda r:(r.spin_rpm,r[ycol]))
    for i,r in enumerate(rows):
        col=CAT.get(r.category,MUTED)
        ax.scatter(r.spin_rpm,r[ycol],s=85,marker=SRC_MK.get(r.src,"o"),c=col,edgecolor="white",lw=1.1,zorder=3)
        dy=10 if i%2==0 else -14
        ax.annotate(f"{str(r['brand']).title()} {clean(r['model'])}",(r.spin_rpm,r[ycol]),
                    textcoords="offset points",xytext=(0,dy),ha="center",fontsize=7.2,
                    color=col,fontweight="bold",zorder=6)
    mark_you(ax,4949,(39.5 if ycol=="descent_deg" else 11.54),"YOU: P770 (GC3, 75mph)",YOU,300,"D",-16)
    zone_rect(ax,5500,"high",y_thr,"high")
    style(ax,title,sub,"Backspin (rpm, robot 7-iron)  ->  more spin",ylab)
    leg=[Line2D([0],[0],marker=mk,color="w",markerfacecolor=MUTED,markersize=9,label=SRC_NAME[s]) for s,mk in SRC_MK.items()]
    leg.append(Line2D([0],[0],marker="D",color="w",markerfacecolor=YOU,markersize=10,label="Your P770 (GC3)"))
    ax.legend(handles=leg,loc="lower right",frameon=False,fontsize=8.5,title="Source (shape)")
    fig.tight_layout(); fig.savefig(OUT/fname,dpi=150); plt.close(fig)
    print(f"wrote outputs/charts/{fname}  ({len(inzone)} in-zone / {len(df)} measured points)")


def pooled_spin_descent():
    _pooled("descent_deg",45.0,
        "Green-holding (ALL 3 robot sources pooled) — spin vs descent",
        "67 measured models. Shape = source; conditions differ (GD 82mph / CC 80mph steel / MGS varies) so compare within a source. Green zone: spin>=5,500 & descent>=45.",
        "Descent angle (deg)  ->  steeper / holds greens","2b_spin_descent_pooled.png")


def pooled_spin_moi():
    _pooled("moi",14.0,
        "Spin vs MOI (ALL 3 robot sources pooled)",
        "Spin measured (shape=source; conditions differ), MOI from Maltby. Green zone: spin>=5,500 & MOI>=14.",
        "MOI (Maltby)  ->  more forgiving","3b_spin_moi_pooled.png",need_moi=True)


if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--since",type=int,default=YEAR_MIN)
    YEAR_MIN=ap.parse_args().since
    print(f"CG charts: year >= {YEAR_MIN}")
    cg_map(); actual_vcog_vs_moi(); eff_vcog_vs_moi(); green_holding(); spin_vs_moi()
    pooled_spin_descent(); pooled_spin_moi()
