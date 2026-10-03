// Regenerates the Material 3 palette in app/static/css/app.css (see DESIGN.md).
//   cd /tmp && npm i @material/material-color-utilities@0.3.0 && node <repo>/study_station/v2/tools/m3_palette.mjs
// Prints the light/dark role values and a WCAG contrast report; copy the values into the --md-* tokens.
import { argbFromHex, hexFromArgb, Hct, SchemeTonalSpot, SchemeFidelity, MaterialDynamicColors as M, TonalPalette, Blend } from '@material/material-color-utilities';
const SEED = argbFromHex('#1A73E8');
const lum = h => { const c=[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255).map(v=>v<=.03928?v/12.92:((v+.055)/1.055)**2.4); return .2126*c[0]+.7152*c[1]+.0722*c[2]; };
const cr = (a,b) => { const [x,y]=[lum(a),lum(b)].sort((p,q)=>q-p); return ((x+.05)/(y+.05)).toFixed(2); };
const custom = (hex, chroma) => { const h = Blend.harmonize(argbFromHex(hex), SEED); const hct = Hct.fromInt(h); return TonalPalette.fromHueAndChroma(hct.hue, chroma); };
const green = custom('#2E7D32', 40), amber = custom('#B26A00', 48), violet = TonalPalette.fromHueAndChroma(Hct.fromInt(argbFromHex('#7C3AED')).hue, 60);
const nv = TonalPalette.fromHueAndChroma(Hct.fromInt(SEED).hue, 6);
const out = {};
for (const dark of [false, true]) {
  const ts = new SchemeTonalSpot(Hct.fromInt(SEED), dark, 0), fi = new SchemeFidelity(Hct.fromInt(SEED), dark, 0);
  const g = r => hexFromArgb(M[r].getArgb(ts)), f = r => hexFromArgb(M[r].getArgb(fi));
  const t = (p, l, d) => hexFromArgb(p.tone(dark ? d : l));
  out[dark?'dark':'light'] = {
    primary: f('primary'), 'on-primary': f('onPrimary'), 'primary-container': g('primaryContainer'), 'on-primary-container': g('onPrimaryContainer'),
    'secondary-container': g('secondaryContainer'), 'on-secondary-container': g('onSecondaryContainer'),
    tertiary: g('tertiary'), 'tertiary-container': g('tertiaryContainer'), 'on-tertiary-container': g('onTertiaryContainer'),
    error: g('error'), 'on-error': g('onError'), 'error-container': g('errorContainer'), 'on-error-container': g('onErrorContainer'),
    surface: g('surface'), 'surface-container-lowest': g('surfaceContainerLowest'), 'surface-container-low': g('surfaceContainerLow'),
    'surface-container': g('surfaceContainer'), 'surface-container-high': g('surfaceContainerHigh'), 'surface-container-highest': g('surfaceContainerHighest'),
    'on-surface': g('onSurface'), 'on-surface-variant': g('onSurfaceVariant'), 'text-3': t(nv, 40, 70),
    outline: g('outline'), 'outline-variant': g('outlineVariant'), 'inverse-surface': g('inverseSurface'), 'inverse-on-surface': g('inverseOnSurface'),
    success: t(green, 40, 80), 'on-success': t(green, 100, 20), 'success-container': t(green, 92, 25), 'on-success-container': t(green, 20, 90),
    warning: t(amber, 40, 80), 'on-warning': t(amber, 100, 20), 'warning-container': t(amber, 92, 25), 'on-warning-container': t(amber, 20, 90),
    review: t(violet, 40, 80), 'on-review': t(violet, 100, 20),
  };
}
console.log(JSON.stringify(out, null, 1));
for (const m of ['light','dark']) { const c = out[m];
  const pairs = [['on-surface','surface'],['on-surface-variant','surface'],['text-3','surface'],['text-3','surface-container-low'],['on-primary','primary'],['primary','surface'],['primary','secondary-container'],['on-secondary-container','secondary-container'],['on-success','success'],['success','success-container'],['on-error','error'],['error','error-container'],['warning','warning-container'],['on-review','review'],['outline','surface'],['on-surface','surface-container-low']];
  console.log(m, pairs.map(([a,b])=>`${a}/${b}=${cr(c[a],c[b])}`).join('  '));
}
const paper = {bg:'#FBF6EC', text:'#2B2620', text2:'#5A5248'};
console.log('paper', cr(paper.text,paper.bg), cr(paper.text2,paper.bg));
