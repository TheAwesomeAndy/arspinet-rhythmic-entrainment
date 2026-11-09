#!/usr/bin/env python3
"""Scan where the trimmed second sits: EEG window = [s+delta, e-(1-delta)] for delta in 0..1 s.
EEG band-passed 0.5-8 Hz, average-referenced, fronto-central mean; features at 256 Hz.
Reports, per delta and feature, the lag of the peak |z| cross-correlation (vs circular-shift null)
and z at 100/150/200 ms. The correct delta gives an auditory-like peak at 100-200 ms."""
import sys, json, numpy as np
from scipy.signal import resample_poly, correlate, butter, sosfiltfilt
from weineck_loader import load_participant
FC=['Fz','FC1','FC2','Cz','F3','F4','C3','C4']
feats_path=sys.argv[1]; subj=sys.argv[2] if len(sys.argv)>2 else '10'
trials=load_participant('/home/user/data_local/weineck2022', subj, feats_path, trim_side='none', verbose=True)
fs=256.0; sos=butter(4,[0.5,8.0],btype='band',fs=fs,output='sos')
def xc(a,b,lo=-0.5,hi=1.0):
    a=(a-a.mean())/(a.std()+1e-12); b=(b-b.mean())/(b.std()+1e-12)
    full=correlate(b,a,mode='full')/len(a); lags=np.arange(-len(a)+1,len(b))/fs; m=(lags>=lo)&(lags<=hi); return lags[m],full[m]
rng=np.random.RandomState(0); out={}
prep=[]
for t in trials:
    X=t['eeg']-t['eeg'].mean(0,keepdims=True)           # average reference (incl. aux ch '33'? exclude it)
    names=t['ch_names']; keep=[i for i,c in enumerate(names) if c!='33']
    X=t['eeg'][keep]; X=X-X.mean(0,keepdims=True); X=sosfiltfilt(sos,X,axis=1)
    idx=[names.index(c) for c in FC if c in names]; idx=[keep.index(i) for i in idx]
    prep.append((X[idx].mean(0), t['feats']))
for delta in (0.0,0.25,0.5,0.75,1.0):
    out[delta]={}
    for fi,fname in ((3,'spec_flux'),(2,'beat_onsets'),(0,'envelope')):
        acc=None; nulls=[]
        for eeg_full,F in prep:
            feat=resample_poly(F[fi],2,1); n=len(feat); off=int(round(delta*fs))
            eeg=eeg_full[off:off+n]; n=min(len(eeg),n); eeg,feat=eeg[:n],feat[:n]
            lags,c=xc(feat,eeg); acc=c if acc is None else acc+c
            ms=int(3*fs); nulls.append([xc(np.roll(feat,rng.randint(ms,n-ms)),eeg)[1] for _ in range(30)])
        acc/=len(prep); null=np.mean(np.array(nulls),0); z=(acc-null.mean(0))/(null.std(0)+1e-12)
        ip=np.argmax(np.abs(z)); zz=lambda L: z[np.argmin(np.abs(lags-L))]
        print(f"delta={delta:.2f} {fname:>11}: peak z={z[ip]:+5.1f} at {lags[ip]*1000:+5.0f} ms | z@50={zz(0.05):+.1f} @100={zz(0.1):+.1f} @150={zz(0.15):+.1f} @200={zz(0.2):+.1f} @250={zz(0.25):+.1f}")
        out[delta][fname]={'peak_z':float(z[ip]),'peak_lag_ms':float(lags[ip]*1000)}
json.dump(out,open(f'results/align_scan_subj{subj}.json','w'),indent=1)
