import json, re, statistics
from collections import defaultdict

PROP_FULL = ['psa','alogp','hba','hbd','mw','qed','ro5_viol',
             'aromatic_rings','heavy_atoms','np_likeness','rtb','ro3_pass']
PROP_TR   = ['psa','alogp','hbd','qed','np_likeness']
ALERTS    = ['PAINS','Glaxo','BMS','Dundee','MLSMR']


def text_parse(resp):
    out = {}
    if not isinstance(resp, str): return out
    for l in resp.splitlines():
        l = l.strip()
        if '=' in l:
            k, v = l.split('=', 1); out[k.strip()] = v.strip()
    return out


def num(s):
    if s is None: return None
    if isinstance(s, (int, float, bool)): return float(s)
    s = str(s).strip().lower()
    if s in ('yes','true'):  return 1.0
    if s in ('no','false'):  return 0.0
    m = re.search(r'-?\d+\.?\d*', s)
    return float(m.group()) if m else None


def to_bool(s):
    if isinstance(s, bool): return s
    if isinstance(s, (int, float)): return bool(s)
    if not isinstance(s, str): return None
    s = s.strip().lower()
    if s in ('yes','true','1'):  return True
    if s in ('no','false','0'):  return False
    return None


def dir_correct(dp, dg):
    """user convention: dp==0 → wrong when dg!=0; else sign match."""
    if dg == 0: return None
    if dp == 0: return False
    return (dp > 0) == (dg > 0)


def eval_task1(path):
    data = json.load(open(path))
    n = len(data)
    n_sr = 0
    prop_errs  = {k: [] for k in PROP_FULL}
    alert_corr = {a: 0 for a in ALERTS}; alert_tot = {a: 0 for a in ALERTS}
    bio_errs = []
    for r in data:
        parsed = r.get('parsed') if isinstance(r.get('parsed'), dict) else text_parse(r.get('response',''))
        if not parsed: continue
        gt = r['gt']
        # require all 12 props + 5 alerts present
        if not (set(PROP_FULL) | set(ALERTS)).issubset(set(parsed.keys())):
            continue
        n_sr += 1
        for k in PROP_FULL:
            p = num(parsed.get(k))
            g = num(gt['combined_properties'].get(k))
            if p is not None and g is not None:
                prop_errs[k].append(abs(p-g))
        for a in ALERTS:
            p = to_bool(parsed.get(a))
            if p is None: continue
            g = bool(gt['combined_alerts'].get(a))
            alert_tot[a] += 1
            if p == g: alert_corr[a] += 1
        # bio: prompt-listed targets, exact key match in parsed/response
        bio_targets = []
        if 'Bioactivity targets to predict' in r.get('prompt',''):
            ib = False
            for line in r['prompt'].splitlines():
                if 'Bioactivity targets to predict' in line: ib=True; continue
                if ib and line.strip().startswith('-'):
                    bio_targets.append(line.strip().lstrip('-').strip())
        gt_bio = {}
        for b in gt.get('combined_bioactivity', []):
            org = b.get('organism') or b.get('target_organism')
            label = f'{b["stype"]} on {b.get("target")} ({org})' if org else f'{b["stype"]} on {b.get("target")}'
            gt_bio[label] = b.get('pchembl')
        for tgt in bio_targets:
            p = num(parsed.get(tgt))
            g = gt_bio.get(tgt)
            if p is not None and g is not None:
                bio_errs.append(abs(p - float(g)))

    propMAE  = statistics.mean(statistics.mean(v) for v in prop_errs.values() if v)
    alertAcc = statistics.mean(alert_corr[a]/alert_tot[a] for a in ALERTS if alert_tot[a])
    bioMAE   = statistics.mean(bio_errs) if bio_errs else None
    print(f'=== Task 1 ({path}) n={n} ===')
    print(f'  SR        = {100*n_sr/n:.1f}')
    print(f'  propMAE   = {propMAE:.4f}')
    print(f'  alertAcc  = {alertAcc:.4f}')
    print(f'  bioMAE    = {bioMAE:.4f}')


def eval_task2(path):
    data = json.load(open(path))
    n = len(data)
    n_sr = 0
    dprop_errs  = {k: [] for k in PROP_TR}
    dbio_errs   = []
    dalert_corr = {a: 0 for a in ALERTS}; dalert_tot = {a: 0 for a in ALERTS}
    dir_c = dir_t = 0
    for r in data:
        parsed = r.get('parsed') if isinstance(r.get('parsed'), dict) else text_parse(r.get('response',''))
        if not parsed: continue
        gt = r['gt']
        if not set(gt.keys()).issubset(set(parsed.keys())):
            continue
        n_sr += 1
        for axis, info in gt.items():
            ak = info.get('axis_kind'); sv = info.get('scaffold_value')
            p = parsed.get(axis)
            if p is None: continue
            if ak in ('property','bioactivity'):
                pv = num(p); gv = num(info['expected'])
                try: svf = float(sv)
                except (ValueError, TypeError): continue
                if pv is None or gv is None: continue
                dp = pv - svf; dg = gv - svf
                err = abs(dp - dg)
                if ak == 'property' and axis in dprop_errs:
                    dprop_errs[axis].append(err)
                elif ak == 'bioactivity':
                    dbio_errs.append(err)
                d = dir_correct(dp, dg)
                if d is not None:
                    dir_t += 1
                    if d: dir_c += 1
            elif ak == 'alert':
                pb = to_bool(p)
                if pb is None: continue
                gb = bool(info['expected'])
                dalert_tot[axis] += 1
                if pb == gb: dalert_corr[axis] += 1
                if sv is not None and gb != bool(sv):
                    dir_t += 1
                    if pb == gb: dir_c += 1   # correct iff pred matches expected (= dir matches)

    dpropMAE  = statistics.mean(statistics.mean(v) for v in dprop_errs.values() if v)
    dalertAcc = statistics.mean(dalert_corr[a]/dalert_tot[a] for a in ALERTS if dalert_tot[a])
    dbioMAE   = statistics.mean(dbio_errs) if dbio_errs else None
    dirAcc    = dir_c / dir_t if dir_t else None
    print(f'\n=== Task 2 ({path}) n={n} ===')
    print(f'  SR        = {100*n_sr/n:.1f}')
    print(f'  ΔpropMAE  = {dpropMAE:.4f}')
    print(f'  ΔalertAcc = {dalertAcc:.4f}')
    print(f'  ΔbioMAE   = {dbioMAE:.4f}')
    print(f'  dirAcc    = {dirAcc:.4f}')


def filter_to_subset(src_path, our_path, out_path):
    """Subset src to our 1541-triple test set."""
    ours = json.load(open(our_path))
    triples = {(r['scaffold_smiles'], r['sub_smiles'], r['combined_smiles']) for r in ours}
    src = json.load(open(src_path))
    out = [r for r in src if (r['scaffold_smiles'], r['sub_smiles'], r['combined_smiles']) in triples]
    json.dump(out, open(out_path, 'w'), ensure_ascii=False, indent=2)
    print(f'  filtered {src_path} → {out_path}  ({len(out)} entries)')
    return out_path


if __name__ == '__main__':
    import sys
    paths = sys.argv[1:] or [
        '/data/user16/gpt-5.2_task1.json',
        '/data/user16/gpt-5.2_task2.json',
    ]
    for p in paths:
        if 'task1' in p:
            eval_task1(p)
        else:
            eval_task2(p)
