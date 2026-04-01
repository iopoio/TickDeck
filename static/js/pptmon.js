/**
 * PPTMON v2 — PPTX Rendering Engine
 * Extracted from templates/index.html for caching and maintainability.
 */

const LAYOUT_MAP = {
  corporate_overview:       () => 'split',
  market_shock:             (hasBg) => hasBg ? 'portfolio' : 'comparison',
  market_problem:           (hasBg, n) => n >= 5 ? 'comparison' : 'cards',
  brand_story:              (hasBg, n) => hasBg ? 'portfolio' : (n >= 3 ? 'cards' : 'split'),
  creative_approach:        (hasBg, n) => hasBg ? 'split' : (n >= 3 ? 'two_col_text' : 'split'),
  creative_philosophy:      (hasBg) => hasBg ? 'split' : 'two_col_text',
  market_impact:            (hasBg) => hasBg ? 'portfolio' : 'cards',
  proof_of_concept:         (hasBg) => hasBg ? 'portfolio' : 'cards',
  results:                  (hasBg) => hasBg ? 'portfolio' : 'cards',
  impact:                   (hasBg) => hasBg ? 'portfolio' : 'cards',
  showcase:                 (hasBg) => hasBg ? 'portfolio' : 'split',
  flagship_experience:      (hasBg) => hasBg ? 'portfolio' : 'split',
  case_study:               (hasBg, n) => n >= 5 ? 'comparison' : 'split',
  governance:               () => 'split',
  team_intro:               () => 'cards',
  target_audience:          () => 'cards',
  market_insights:          () => 'split',
  infrastructure_and_scale: (hasBg) => hasBg ? 'portfolio' : 'cards',
  client_list:              () => 'cards',
  service_pillar_1:         () => 'split',
  service_pillar_2:         () => 'cards',
  service_pillar_3:         () => 'portfolio',
  core_business_1:          () => 'split',
  core_business_2:          () => 'cards',
  core_business_3:          () => 'portfolio',
  showcase_work:            (hasBg) => hasBg ? 'portfolio' : 'cards',
  showcase_work_1:          (hasBg) => hasBg ? 'portfolio' : 'cards',
  showcase_work_2:          (hasBg) => hasBg ? 'split' : 'two_col_text',
  showcase_work_3:          () => 'cards',
  key_metrics:              () => 'stat_3col',
  our_process:              () => 'numbered_process',
  company_history:          () => 'timeline_h',
  team_credibility:         (hasBg) => hasBg ? 'portfolio' : 'split',
  curriculum_structure:     () => 'numbered_process',
  how_it_works:             () => 'numbered_process',
  solution_overview:        (hasBg, n) => hasBg ? 'split' : (n >= 3 ? 'two_col_text' : 'cards'),
  pain_analysis:            () => 'numbered_process',
  market_challenge:         (hasBg) => hasBg ? 'portfolio' : 'split',
  proof_results:            (hasBg) => hasBg ? 'portfolio' : 'cards',
  why_us:                   () => 'cards',
  scale_proof:              (hasBg, n) => n >= 3 ? 'stat_3col' : 'split',
  scalability_proof:        (hasBg, n) => n >= 3 ? 'stat_3col' : 'split',
  delivery_model:           () => 'numbered_process',
  ecosystem_partners:       () => 'cards',
  dual_sided_value:         () => 'cards',
};

function _handleCTypeLayout(nt, stype, hasBg) {
  if (nt && nt.toUpperCase() === 'C') {
    if (['showcase_work_1','showcase_work_2','showcase_work_3',
         'showcase','flagship_experience','brand_story'].includes(stype))
      return hasBg ? 'portfolio' : 'cards';
  }
  return null;
}

function _applyLayoutRotationRule(layout, prevLayout, layoutCount) {
  let finalLayout = layout;
  if (prevLayout && finalLayout === prevLayout
      && !['radial','4step','timeline','section','mosaic'].includes(finalLayout)) {
    const rot = ['split','cards','two_col_text','portfolio','comparison'];
    finalLayout = rot[(rot.indexOf(finalLayout) + 1) % rot.length];
  }
  const _numFamily = ['numbered_process','process_cards'];
  if (_numFamily.includes(finalLayout) && _numFamily.includes(prevLayout) && finalLayout !== prevLayout) {
    finalLayout = (layoutCount['split'] || 0) <= (layoutCount['cards'] || 0) ? 'split' : 'cards';
  }
  const _FIXED = ['cover','cta','toc','section','radial','4step','timeline','mosaic',
                  'timeline_h','circle4','converge4','linked4','gear','swot4',
                  'kpi_cards','timeline_bars','ruled_list',
                  'numbered_process','process_cards','data_table',
                  'stat_3col','stat_grid','timeline_v','comparison_vs',
                  'matrix_2x2','bar_chart',
                  'pull_quote','big_statement','two_col_text','problem_solution',
                  'market_circles','checklist_pills','asymmetric_1_3'];
  const MAX_USE = 2;
  if (!_FIXED.includes(finalLayout) && (layoutCount[finalLayout] || 0) >= MAX_USE) {
    const rot = ['split','cards','two_col_text','portfolio','comparison'];
    const sorted = rot.filter(l => l !== finalLayout)
                      .sort((a, b) => (layoutCount[a] || 0) - (layoutCount[b] || 0));
    if (sorted.length) finalLayout = sorted[0];
  }
  return finalLayout;
}

// getSlideLayout(slideOrType, nt, prevLayout, layoutCount)
function getSlideLayout(slideOrType, nt, prevLayout, layoutCount = {}) {
  const stype  = typeof slideOrType === 'string' ? slideOrType : (slideOrType?.type || '');
  const body   = (typeof slideOrType === 'object' && slideOrType !== null)
                   ? (Array.isArray(slideOrType.body) ? slideOrType.body : []) : [];
  const hasBg  = (typeof slideOrType === 'object' && slideOrType !== null)
                   ? !!(slideOrType.bg_b64) : false;
  const n = body.length;

  // ── 고정 구조 ──
  if (['cover','title_identity'].includes(stype)) return 'cover';
  if (['cta_session','contact','cta'].includes(stype)) return 'cta';
  if (['toc','table_of_contents','index'].includes(stype)) return 'toc';
  if (['section_intro','chapter_break','section_break','section_header',
       'section_divider'].includes(stype)) return 'section';
  if (['mosaic','service_overview','product_overview','features_overview',
       'showcase_overview','business_areas','service_matrix'].includes(stype)) return 'mosaic';

  // ── C-type 전용 ──
  const cTypeLayout = _handleCTypeLayout(nt, stype, hasBg);
  if (cTypeLayout) return cTypeLayout;

  // ── 신규 구조형 (조기 반환) ──
  if (['problem_solution','before_after_compare','asis_tobe','problem_vs_solution'].includes(stype)) return 'problem_solution';
  if (['pull_quote','key_insight','big_insight','testimonial','quote_slide','insight'].includes(stype)) return 'pull_quote';
  if (!hasBg && n === 0 && ['market_shock','impact'].includes(stype)) return 'pull_quote';
  if (['big_statement','impact_statement','key_message','bold_claim','brand_statement'].includes(stype)) return 'big_statement';

  if (['agenda','toc_detail','objectives','goals','issues_risks','mitigation_plan','action_items','next_steps_detail','comparison_text','two_col'].includes(stype)) return 'two_col_text';
  if (['why_us'].includes(stype)) {
    const _whyBase = (layoutCount['two_col_text'] || 0) >= 1 ? 'cards' : 'two_col_text';
    if (_whyBase === prevLayout) return (layoutCount['numbered_process'] || 0) >= 1 ? 'split' : 'numbered_process';
    return _whyBase;
  }
  
  if (!hasBg && n >= 5 && n <= 6 && ['platform_overview','product_suite','service_breakdown'].includes(stype)) return 'asymmetric_1_3';
  if (!hasBg && n >= 4 && ['solution_overview','team_intro','client_list'].includes(stype)) return 'two_col_text';
  if (!hasBg && n >= 4 && ['why_us'].includes(stype)) {
    const _whyBase4 = (layoutCount['two_col_text'] || 0) >= 1 ? 'cards' : 'two_col_text';
    if (_whyBase4 === prevLayout) return (layoutCount['numbered_process'] || 0) >= 1 ? 'split' : 'numbered_process';
    return _whyBase4;
  }

  if (['market_size','tam_sam_som','addressable_market','market_sizing','target_market_size'].includes(stype)) return 'market_circles';
  if (['metrics','kpi','statistics','impact_numbers','results_overview','performance_metrics','growth_metrics','financial_highlights','business_results'].includes(stype)) return 'kpi_cards';
  if (['evolution','annual_progress','growth_history','year_over_year','performance_timeline','annual_comparison','bar_timeline'].includes(stype)) return 'timeline_bars';
  if (['principles','guidelines','policy','core_principles','guiding_principles','our_principles','commitments','manifesto','framework_items','rules','standards'].includes(stype)) return 'ruled_list';
  if (['process_steps','implementation_steps','workflow_steps','action_plan','execution_steps','how_it_works','our_process','methodology','approach','step_by_step','onboarding_steps','delivery_process','work_process'].includes(stype)) return (layoutCount['numbered_process'] || 0) >= 1 ? 'process_cards' : 'numbered_process';

  if (['proof_results','case_study_result'].includes(stype) && typeof slideOrType === 'object' && (slideOrType?.infographic?.data?.stats || []).length >= 2) return 'kpi_cards';
  if (['proof_results','case_study_result'].includes(stype) && typeof slideOrType === 'object' && (slideOrType?.infographic?.data?.stats || []).length < 2 && n >= 2 && n <= 8) return 'checklist_pills';
  if (['market_impact','scale_proof','case_study','scalability_proof','performance_data'].includes(stype) && n > 0 && n <= 4) return 'stat_3col';
  if (['proof_results','scale_proof','metrics','performance_metrics','business_results','financial_highlights'].includes(stype) && n >= 5) return 'stat_grid';
  
  if (['company_history','growth_story','our_story','brand_history','milestones','achievements'].includes(stype)) return 'timeline_h';
  if (['roadmap'].includes(stype)) return 'timeline_v';
  if (['competitive_analysis','market_comparison','before_after','solution_comparison'].includes(stype)) return 'comparison_vs';
  if (['feature_comparison','comparison_table','pricing_table','feature_matrix','specs_comparison','product_comparison','option_matrix','tier_comparison','service_tiers','plan_comparison'].includes(stype)) return 'data_table';
  if (['swot_analysis','swot'].includes(stype)) return 'swot4';
  if (['positioning_matrix','matrix_2x2','bcg_matrix','ansoff_matrix','competitive_matrix','comparison_matrix','risk_impact_matrix'].includes(stype)) return 'matrix_2x2';
  
  if (typeof slideOrType === 'object' && slideOrType !== null && Array.isArray(slideOrType?.chart_data?.values) && slideOrType.chart_data.values.length >= 2) return 'bar_chart';
  if (['competitive_analysis','risk_matrix','risk_assessment','interdependencies','mutual_factors','competitive_matrix','four_forces'].includes(stype)) return 'linked4';
  if (['gear_process','operations_cycle','platform_ecosystem','service_ecosystem','circular_process','flywheel','ecosystem'].includes(stype)) return 'gear';
  if (['schedule','project_plan','project_timeline','quarterly_plan','annual_plan','delivery_schedule','implementation_schedule','sprint_plan','phased_rollout'].includes(stype)) return 'timeline_h';
  if (['convergence_model','strategic_convergence','four_pillars_model','value_creation','success_factors'].includes(stype)) return 'converge4';
  if (['value_proposition','brand_pillars','four_pillars','strategic_pillars','value_stack','framework'].includes(stype)) return n === 4 ? 'converge4' : 'radial';
  
  if (['timeline','roadmap','history','milestones','journey','company_history','growth_story','evolution','trajectory','our_story','brand_history','achievements'].includes(stype)) return 'timeline';
  if (['our_process','how_it_works','service_workflow','implementation','onboarding','delivery_process','workflow','proprietary_methodology','approach','methodology','solution_approach','how_we_work','process','steps'].includes(stype)) return '4step';
  
  if (n === 4 && ['key_features','service_features','product_benefits','market_segments','client_types','key_differentiators','four_elements','core_capabilities','product_features'].includes(stype)) return 'circle4';
  if (['core_values','pillars','core_philosophy','creative_philosophy','our_values','brand_values','philosophy','competitive_advantage','differentiators','key_strengths'].includes(stype)) return 'radial';

  // ── 배경 없는 슬라이드 ──
  if (!hasBg) {
    if (['market_challenge','market_problem','problem_statement','challenge','market_shock'].includes(stype)) return 'ruled_list';
    if (['pain_analysis','pain_points'].includes(stype)) return (layoutCount['numbered_process'] || 0) >= 1 ? 'process_cards' : 'numbered_process';
    if (['market_insights','market_analysis','industry_trends','market_overview','competitive_landscape'].includes(stype)) return 'timeline_bars';
    if (['proof_of_concept','results','impact','market_impact','performance_data','infrastructure_and_scale'].includes(stype)) return n <= 3 ? 'stat_3col' : 'kpi_cards';
    if (['corporate_overview','company_overview','about_us'].includes(stype)) return 'radial';
    if (['our_solution','proprietary_methodology','methodology','solution'].includes(stype)) return n >= 4 ? 'numbered_process' : 'radial';
    if (['solution_overview'].includes(stype)) return n >= 4 ? ((layoutCount['two_col_text'] || 0) >= 1 ? 'cards' : 'two_col_text') : 'split';
    if (['governance','compliance','trust','case_study'].includes(stype)) return 'ruled_list';
  }

  // ── 기본값 (LAYOUT_MAP 활용) ──
  let layout = '';
  const mapFn = LAYOUT_MAP[stype];
  if (mapFn) {
    layout = mapFn(hasBg, n);
  } else {
    if (n >= 4)     layout = 'cards';
    else if (n <= 1) layout = hasBg ? 'portfolio' : 'split';
    else             layout = hasBg ? 'split' : 'cards';
  }

  return _applyLayoutRotationRule(layout, prevLayout, layoutCount);
}

// ════════════════════════════════════════════════════════
// PPTMON v2 — 색상 시스템 (pptmon_template_v2.js 기반)
// ════════════════════════════════════════════════════════
function _pm_hx(hex) {
  const h = hex.replace('#','');
  return { r: parseInt(h.slice(0,2),16), g: parseInt(h.slice(2,4),16), b: parseInt(h.slice(4,6),16) };
}
function _pm_rgb(r,g,b) {
  return [r,g,b].map(v=>Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,'0')).join('').toUpperCase();
}
function _pm_bright(hex, amt) {
  const {r,g,b}=_pm_hx(hex);
  return amt>=0 ? _pm_rgb(r+(255-r)*amt,g+(255-g)*amt,b+(255-b)*amt) : _pm_rgb(r*(1+amt),g*(1+amt),b*(1+amt));
}
function _pm_light(hex) { const {r,g,b}=_pm_hx(hex); return (0.299*r+0.587*g+0.114*b)/255>0.5; }
// HSL 기반 채도 유지 tint/shade — 프리미엄 컬러 베리에이션
function _pm_toHsl(hex) {
  let {r,g,b} = _pm_hx(hex); r/=255; g/=255; b/=255;
  const max=Math.max(r,g,b), min=Math.min(r,g,b), l=(max+min)/2;
  if (max===min) return {h:0,s:0,l};
  const d=max-min, s=l>0.5?d/(2-max-min):d/(max+min);
  let h = max===r?(g-b)/d+(g<b?6:0) : max===g?(b-r)/d+2 : (r-g)/d+4;
  return {h:h/6*360, s, l};
}
function _pm_fromHsl(h,s,l) {
  const hue2rgb=(p,q,t)=>{if(t<0)t+=1;if(t>1)t-=1;if(t<1/6)return p+(q-p)*6*t;if(t<1/2)return q;if(t<2/3)return p+(q-p)*(2/3-t)*6;return p;};
  if(s===0){const v=Math.round(l*255);return _pm_rgb(v,v,v);}
  const q=l<0.5?l*(1+s):l+s-l*s, p=2*l-q;
  return _pm_rgb(hue2rgb(p,q,h/360+1/3)*255, hue2rgb(p,q,h/360)*255, hue2rgb(p,q,h/360-1/3)*255);
}
// 채도 유지하면서 밝기만 조절 (amt>0: 밝게, <0: 어둡게)
function _pm_hslShift(hex, lAmt, sAmt=0) {
  const {h,s,l} = _pm_toHsl(hex);
  return _pm_fromHsl(h, Math.max(0,Math.min(1,s*(1+sAmt))), Math.max(0,Math.min(1,l+lAmt)));
}
function createColorSystem(primary, bg) {
  primary = (primary||'').replace('#','') || '6C47FF';
  bg      = (bg||'').replace('#','')      || 'FFFFFF';
  const L = _pm_light(bg);
  // 프리미엄 베리에이션: HSL 기반으로 채도 유지하면서 밝기 조절
  // accentLight: 밝기 +0.22, 채도 -15% → 탁해지지 않는 rich tint
  // accentDeep:  밝기 -0.22, 채도 +8% → 깊고 풍부한 shade
  const _accentLight = _pm_hslShift(primary, 0.22, -0.15);
  // 틴티드 뉴트럴: primary hue를 극소량 섞은 다크/라이트 (컬러 온도 통일)
  const _tintedDark  = _pm_hslShift(primary, -0.42, -0.75);  // 거의 검정이지만 primary 색조
  const _tintedLight = _pm_hslShift(primary,  0.42, -0.80);  // 거의 흰색이지만 primary 색조
  const _tintedGray  = _pm_hslShift(primary,  0.05, -0.65);  // 중간 회색에 primary 색조
  return {
    primary, bg,
    textPrimary:   L ? '111111' : 'F5F5F5',
    textSecondary: L ? '444455' : 'BBBBBB',
    textMuted:     L ? 'AAAAAA' : '777777',
    textOnPrimary: _pm_light(primary) ? '111111' : 'FFFFFF',
    textOnAccentLight: _pm_light(_accentLight) ? '111111' : 'FFFFFF',
    accentLight:   _accentLight,
    accentDark:    _pm_hslShift(primary, -0.22,  0.08),
    lineColor:     L ? _pm_bright(bg,-0.15) : _pm_bright(bg,0.20),
    headerBarBg:   L ? _pm_bright(bg, -0.07) : _pm_bright(bg, 0.18),
    // 세련된 뉴트럴 (primary 색조 포함 — 컬러 온도 통일)
    tintedDark:    _tintedDark,   // 커버/CTA 배경용 (순수 검정 대체)
    tintedLight:   _tintedLight,  // 라이트 배경용 (순수 흰색 대체)
    tintedGray:    _tintedGray,   // 보조 텍스트용 (순수 회색 대체)
  };
}


// ════════════════════════════════════════════════════════
// Lucide 아이콘 세트 (50개 — SVG base64, white stroke)
// 용도: pm_addIcon() 호출 시 아이콘 이름으로 조회
// Fallback: ICON_SET['target'] (항상 존재)
// ════════════════════════════════════════════════════════
const ICON_SET = {
  'target': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI2Ii8+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMiIvPjwvc3ZnPg==',
  'briefcase': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjE0IiB4PSIyIiB5PSI3IiByeD0iMiIvPjxwYXRoIGQ9Ik0xNiAyMVY1YTIgMiAwIDAgMC0yLTJoLTRhMiAyIDAgMCAwLTIgMnYxNiIvPjwvc3ZnPg==',
  'building': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3Qgd2lkdGg9IjE2IiBoZWlnaHQ9IjIwIiB4PSI0IiB5PSIyIiByeD0iMiIvPjxwYXRoIGQ9Ik05IDIyVjEyaDZ2MTAiLz48cGF0aCBkPSJNOCA3aC4wMSIvPjxwYXRoIGQ9Ik0xMiA3aC4wMSIvPjxwYXRoIGQ9Ik0xNiA3aC4wMSIvPjxwYXRoIGQ9Ik04IDExaC4wMSIvPjxwYXRoIGQ9Ik0xMiAxMWguMDEiLz48cGF0aCBkPSJNMTYgMTFoLjAxIi8+PC9zdmc+',
  'building-2': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTYgMjJWNGEyIDIgMCAwIDEgMi0yaDhhMiAyIDAgMCAxIDIgMnYxOFoiLz48cGF0aCBkPSJNNiAxMkg0YTIgMiAwIDAgMC0yIDJ2NmEyIDIgMCAwIDAgMiAyaDIiLz48cGF0aCBkPSJNMTggOWgyYTIgMiAwIDAgMSAyIDJ2OWEyIDIgMCAwIDEtMiAyaC0yIi8+PHBhdGggZD0iTTEwIDZoNCIvPjxwYXRoIGQ9Ik0xMCAxMGg0Ii8+PHBhdGggZD0iTTEwIDE0aDQiLz48cGF0aCBkPSJNMTAgMThoNCIvPjwvc3ZnPg==',
  'award': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0ibTE1LjQ3NyAxMi44OSAxLjUxNSA4LjUyNmEuNS41IDAgMCAxLS44MS40N2wtMy41OC0yLjY4N2ExIDEgMCAwIDAtMS4xOTcgMGwtMy41ODYgMi42ODZhLjUuNSAwIDAgMS0uODEtLjQ2OWwxLjUxNC04LjUyNiIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iOCIgcj0iNiIvPjwvc3ZnPg==',
  'trophy': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTYgOUg0LjVhMi41IDIuNSAwIDAgMSAwLTVINiIvPjxwYXRoIGQ9Ik0xOCA5aDEuNWEyLjUgMi41IDAgMCAwIDAtNUgxOCIvPjxwYXRoIGQ9Ik00IDIyaDE2Ii8+PHBhdGggZD0iTTEwIDE0LjY2VjE3YzAgLjU1LS40Ny45OC0uOTcgMS4yMUM3Ljg1IDE4Ljc1IDcgMjAuMjQgNyAyMiIvPjxwYXRoIGQ9Ik0xNCAxNC42NlYxN2MwIC41NS40Ny45OC45NyAxLjIxQzE2LjE1IDE4Ljc1IDE3IDIwLjI0IDE3IDIyIi8+PHBhdGggZD0iTTE4IDJINnY3YTYgNiAwIDAgMCAxMiAwVjJaIi8+PC9zdmc+',
  'flag': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTQgMTVzMS0xIDQtMSA1IDIgOCAyIDQtMSA0LTFWM3MtMSAxLTQgMS01LTItOC0yLTQgMS00IDF6Ii8+PGxpbmUgeDE9IjQiIHgyPSI0IiB5MT0iMjIiIHkyPSIxNSIvPjwvc3ZnPg==',
  'rocket': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTQuNSAxNi41Yy0xLjUgMS4yNi0yIDUtMiA1czMuNzQtLjUgNS0yYy43MS0uODQuNy0yLjEzLS4wOS0yLjkxYTIuMTggMi4xOCAwIDAgMC0yLjkxLS4wOXoiLz48cGF0aCBkPSJtMTIgMTUtMy0zYTIyIDIyIDAgMCAxIDItMy45NUExMi44OCAxMi44OCAwIDAgMSAyMiAyYzAgMi43Mi0uNzggNy41LTYgMTFhMjIuMzUgMjIuMzUgMCAwIDEtNCAyeiIvPjxwYXRoIGQ9Ik05IDEySDRzLjU1LTMuMDMgMi00YzEuNjItMS4wOCA1IDAgNSAwIi8+PHBhdGggZD0iTTEyIDE1djVzMy4wMy0uNTUgNC0yYzEuMDgtMS42MiAwLTUgMC01Ii8+PC9zdmc+',
  'compass': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cG9seWdvbiBwb2ludHM9IjE2LjI0IDcuNzYgMTQuMTIgMTQuMTIgNy43NiAxNi4yNCA5Ljg4IDkuODggMTYuMjQgNy43NiIvPjwvc3ZnPg==',
  'handshake': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0ibTExIDE3IDIgMmExIDEgMCAxIDAgMy0zIi8+PHBhdGggZD0ibTE0IDE0IDIuNSAyLjVhMSAxIDAgMSAwIDMtM2wtMy44OC0zLjg4YTMgMyAwIDAgMC00LjI0IDBsLS44OC44OGExIDEgMCAxIDEtMy0zbDIuODEtMi44MWE1Ljc5IDUuNzkgMCAwIDEgNy4wNi0uODdsLjQ3LjI4YTIgMiAwIDAgMCAxLjQyLjI1TDIxIDQiLz48cGF0aCBkPSJtMjEgMyAxIDExaC0xIi8+PHBhdGggZD0iTTMgMyAyIDE0bDYuNSA2LjVhMSAxIDAgMSAwIDMtMyIvPjxwYXRoIGQ9Ik0zIDRoOCIvPjwvc3ZnPg==',
  'bar-chart': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGxpbmUgeDE9IjEyIiB4Mj0iMTIiIHkxPSIyMCIgeTI9IjEwIi8+PGxpbmUgeDE9IjE4IiB4Mj0iMTgiIHkxPSIyMCIgeTI9IjQiLz48bGluZSB4MT0iNiIgeDI9IjYiIHkxPSIyMCIgeTI9IjE2Ii8+PC9zdmc+',
  'bar-chart-2': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGxpbmUgeDE9IjE4IiB4Mj0iMTgiIHkxPSIyMCIgeTI9IjEwIi8+PGxpbmUgeDE9IjEyIiB4Mj0iMTIiIHkxPSIyMCIgeTI9IjQiLz48bGluZSB4MT0iNiIgeDI9IjYiIHkxPSIyMCIgeTI9IjE0Ii8+PC9zdmc+',
  'trending-up': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjIgNyAxMy41IDE1LjUgOC41IDEwLjUgMiAxNyIvPjxwb2x5bGluZSBwb2ludHM9IjE2IDcgMjIgNyAyMiAxMyIvPjwvc3ZnPg==',
  'trending-down': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjIgMTcgMTMuNSA4LjUgOC41IDEzLjUgMiA3Ii8+PHBvbHlsaW5lIHBvaW50cz0iMTYgMTcgMjIgMTcgMjIgMTEiLz48L3N2Zz4=',
  'pie-chart': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIxLjIxIDE1Ljg5QTEwIDEwIDAgMSAxIDggMi44MyIvPjxwYXRoIGQ9Ik0yMiAxMkExMCAxMCAwIDAgMCAxMiAydjEweiIvPjwvc3ZnPg==',
  'activity': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjIgMTIgMTggMTIgMTUgMjEgOSAzIDYgMTIgMiAxMiIvPjwvc3ZnPg==',
  'percent': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGxpbmUgeDE9IjE5IiB4Mj0iNSIgeTE9IjUiIHkyPSIxOSIvPjxjaXJjbGUgY3g9IjYuNSIgY3k9IjYuNSIgcj0iMi41Ii8+PGNpcmNsZSBjeD0iMTcuNSIgY3k9IjE3LjUiIHI9IjIuNSIvPjwvc3ZnPg==',
  'calculator': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3Qgd2lkdGg9IjE2IiBoZWlnaHQ9IjIwIiB4PSI0IiB5PSIyIiByeD0iMiIvPjxsaW5lIHgxPSI4IiB4Mj0iMTYiIHkxPSI2IiB5Mj0iNiIvPjxsaW5lIHgxPSIxNiIgeDI9IjE2IiB5MT0iMTQiIHkyPSIxOCIvPjxwYXRoIGQ9Ik0xNiAxMGguMDEiLz48cGF0aCBkPSJNMTIgMTBoLjAxIi8+PHBhdGggZD0iTTggMTBoLjAxIi8+PHBhdGggZD0iTTEyIDE0aC4wMSIvPjxwYXRoIGQ9Ik04IDE0aC4wMSIvPjxwYXRoIGQ9Ik0xMiAxOGguMDEiLz48cGF0aCBkPSJNOCAxOGguMDEiLz48L3N2Zz4=',
  'users': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTE2IDIxdi0yYTQgNCAwIDAgMC00LTRINmE0IDQgMCAwIDAtNCA0djIiLz48Y2lyY2xlIGN4PSI5IiBjeT0iNyIgcj0iNCIvPjxwYXRoIGQ9Ik0yMiAyMXYtMmE0IDQgMCAwIDAtMy0zLjg3Ii8+PHBhdGggZD0iTTE2IDMuMTNhNCA0IDAgMCAxIDAgNy43NSIvPjwvc3ZnPg==',
  'user': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIwIDIxdi0yYTQgNCAwIDAgMC00LTRIOGE0IDQgMCAwIDAtNCA0djIiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiLz48L3N2Zz4=',
  'user-check': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTE2IDIxdi0yYTQgNCAwIDAgMC00LTRINmE0IDQgMCAwIDAtNCA0djIiLz48Y2lyY2xlIGN4PSI5IiBjeT0iNyIgcj0iNCIvPjxwb2x5bGluZSBwb2ludHM9IjE2IDExIDE4IDEzIDIyIDkiLz48L3N2Zz4=',
  'user-plus': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTE2IDIxdi0yYTQgNCAwIDAgMC00LTRINmE0IDQgMCAwIDAtNCA0djIiLz48Y2lyY2xlIGN4PSI5IiBjeT0iNyIgcj0iNCIvPjxsaW5lIHgxPSIxOSIgeDI9IjE5IiB5MT0iOCIgeTI9IjE0Ii8+PGxpbmUgeDE9IjIyIiB4Mj0iMTYiIHkxPSIxMSIgeTI9IjExIi8+PC9zdmc+',
  'heart': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTE5IDE0YzEuNDktMS40NiAzLTMuMjEgMy01LjVBNS41IDUuNSAwIDAgMCAxNi41IDNjLTEuNzYgMC0zIC41LTQuNSAyLTEuNS0xLjUtMi43NC0yLTQuNS0yQTUuNSA1LjUgMCAwIDAgMiA4LjVjMCAyLjMgMS41IDQuMDUgMyA1LjVsNyA3WiIvPjwvc3ZnPg==',
  'star': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlnb24gcG9pbnRzPSIxMiAyIDE1LjA5IDguMjYgMjIgOS4yNyAxNyAxNC4xNCAxOC4xOCAyMS4wMiAxMiAxNy43NyA1LjgyIDIxLjAyIDcgMTQuMTQgMiA5LjI3IDguOTEgOC4yNiAxMiAyIi8+PC9zdmc+',
  'mail': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjE2IiB4PSIyIiB5PSI0IiByeD0iMiIvPjxwYXRoIGQ9Im0yMiA3LTguOTcgNS43YTEuOTQgMS45NCAwIDAgMS0yLjA2IDBMMiA3Ii8+PC9zdmc+',
  'phone': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIyIDE2LjkydjNhMiAyIDAgMCAxLTIuMTggMiAxOS43OSAxOS43OSAwIDAgMS04LjYzLTMuMDdBMTkuNSAxOS41IDAgMCAxIDQuNjkgMTNhMTkuNzkgMTkuNzkgMCAwIDEtMy4wNy04LjY3QTIgMiAwIDAgMSAzLjYgMmgzYTIgMiAwIDAgMSAyIDEuNzIgMTIuODQgMTIuODQgMCAwIDAgLjcgMi44MSAyIDIgMCAwIDEtLjQ1IDIuMTFMOC4wOSA5LjkxYTE2IDE2IDAgMCAwIDYgNmwxLjI3LTEuMjdhMiAyIDAgMCAxIDIuMTEtLjQ1IDEyLjg0IDEyLjg0IDAgMCAwIDIuODEuN0EyIDIgMCAwIDEgMjIgMTYuOTJ6Ii8+PC9zdmc+',
  'message-circle': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0ibTMgMjEgMS45LTUuN2E4LjUgOC41IDAgMSAxIDMuOCAzLjh6Ii8+PC9zdmc+',
  'bell': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTYgOGE2IDYgMCAwIDEgMTIgMGMwIDcgMyA5IDMgOUgzczMtMiAzLTkiLz48cGF0aCBkPSJNMTAuMyAyMWExLjk0IDEuOTQgMCAwIDAgMy40IDAiLz48L3N2Zz4=',
  'share-2': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTgiIGN5PSI1IiByPSIzIi8+PGNpcmNsZSBjeD0iNiIgY3k9IjEyIiByPSIzIi8+PGNpcmNsZSBjeD0iMTgiIGN5PSIxOSIgcj0iMyIvPjxsaW5lIHgxPSI4LjU5IiB4Mj0iMTUuNDIiIHkxPSIxMy41MSIgeTI9IjE3LjQ5Ii8+PGxpbmUgeDE9IjE1LjQxIiB4Mj0iOC41OSIgeTE9IjYuNTEiIHkyPSIxMC40OSIvPjwvc3ZnPg==',
  'link': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTEwIDEzYTUgNSAwIDAgMCA3LjU0LjU0bDMtM2E1IDUgMCAwIDAtNy4wNy03LjA3bC0xLjcyIDEuNzEiLz48cGF0aCBkPSJNMTQgMTFhNSA1IDAgMCAwLTcuNTQtLjU0bC0zIDNhNSA1IDAgMCAwIDcuMDcgNy4wN2wxLjcxLTEuNzEiLz48L3N2Zz4=',
  'cpu': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3Qgd2lkdGg9IjE2IiBoZWlnaHQ9IjE2IiB4PSI0IiB5PSI0IiByeD0iMiIvPjxyZWN0IHdpZHRoPSI2IiBoZWlnaHQ9IjYiIHg9IjkiIHk9IjkiIHJ4PSIxIi8+PHBhdGggZD0iTTE1IDJ2MiIvPjxwYXRoIGQ9Ik0xNSAyMHYyIi8+PHBhdGggZD0iTTIgMTVoMiIvPjxwYXRoIGQ9Ik0yIDloMiIvPjxwYXRoIGQ9Ik0yMCAxNWgyIi8+PHBhdGggZD0iTTIwIDloMiIvPjxwYXRoIGQ9Ik05IDJ2MiIvPjxwYXRoIGQ9Ik05IDIwdjIiLz48L3N2Zz4=',
  'database': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGVsbGlwc2UgY3g9IjEyIiBjeT0iNSIgcng9IjkiIHJ5PSIzIi8+PHBhdGggZD0iTTMgNVYxOUE5IDMgMCAwIDAgMjEgMTlWNSIvPjxwYXRoIGQ9Ik0zIDEyQTkgMyAwIDAgMCAyMSAxMiIvPjwvc3ZnPg==',
  'cloud': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTE3LjUgMTlIOWE3IDcgMCAxIDEgNi43MS05aDEuNzlhNC41IDQuNSAwIDEgMSAwIDlaIi8+PC9zdmc+',
  'wifi': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTUgMTNhMTAgMTAgMCAwIDEgMTQgMCIvPjxwYXRoIGQ9Ik04LjUgMTYuNWE1IDUgMCAwIDEgNyAwIi8+PHBhdGggZD0iTTIgOC44MmExNSAxNSAwIDAgMSAyMCAwIi8+PGxpbmUgeDE9IjEyIiB4Mj0iMTIuMDEiIHkxPSIyMCIgeTI9IjIwIi8+PC9zdmc+',
  'lock': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3Qgd2lkdGg9IjE4IiBoZWlnaHQ9IjExIiB4PSIzIiB5PSIxMSIgcng9IjIiIHJ5PSIyIi8+PHBhdGggZD0iTTcgMTFWN2E1IDUgMCAwIDEgMTAgMHY0Ii8+PC9zdmc+',
  'code': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMTYgMTggMjIgMTIgMTYgNiIvPjxwb2x5bGluZSBwb2ludHM9IjggNiAyIDEyIDggMTgiLz48L3N2Zz4=',
  'layers': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlnb24gcG9pbnRzPSIxMiAyIDIgNyAxMiAxMiAyMiA3IDEyIDIiLz48cG9seWxpbmUgcG9pbnRzPSIyIDE3IDEyIDIyIDIyIDE3Ii8+PHBvbHlsaW5lIHBvaW50cz0iMiAxMiAxMiAxNyAyMiAxMiIvPjwvc3ZnPg==',
  'globe': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48bGluZSB4MT0iMiIgeDI9IjIyIiB5MT0iMTIiIHkyPSIxMiIvPjxwYXRoIGQ9Ik0xMiAyYTE1LjMgMTUuMyAwIDAgMSA0IDEwIDE1LjMgMTUuMyAwIDAgMS00IDEwIDE1LjMgMTUuMyAwIDAgMS00LTEwIDE1LjMgMTUuMyAwIDAgMSA0LTEweiIvPjwvc3ZnPg==',
  'arrow-right': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTUgMTJoMTQiLz48cGF0aCBkPSJtMTIgNSA3IDctNyA3Ii8+PC9zdmc+',
  'check-circle': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIyIDExLjA4VjEyYTEwIDEwIDAgMSAxLTUuOTMtOS4xNCIvPjxwb2x5bGluZSBwb2ludHM9IjIyIDQgMTIgMTQuMDEgOSAxMS4wMSIvPjwvc3ZnPg==',
  'x-circle': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJtMTUgOS02IDYiLz48cGF0aCBkPSJtOSA5IDYgNiIvPjwvc3ZnPg==',
  'refresh-cw': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTMgMTJhOSA5IDAgMCAxIDktOSA5Ljc1IDkuNzUgMCAwIDEgNi43NCAyLjc0TDIxIDgiLz48cGF0aCBkPSJNMjEgM3Y1aC01Ii8+PHBhdGggZD0iTTIxIDEyYTkgOSAwIDAgMS05IDkgOS43NSA5Ljc1IDAgMCAxLTYuNzQtMi43NEwzIDE2Ii8+PHBhdGggZD0iTTggMTZIM3Y1Ii8+PC9zdmc+',
  'clock': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cG9seWxpbmUgcG9pbnRzPSIxMiA2IDEyIDEyIDE2IDE0Ii8+PC9zdmc+',
  'zap': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlnb24gcG9pbnRzPSIxMyAyIDMgMTQgMTIgMTQgMTEgMjIgMjEgMTAgMTIgMTAgMTMgMiIvPjwvc3ZnPg==',
  'settings': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTEyLjIyIDJoLS40NGEyIDIgMCAwIDAtMiAydi4xOGEyIDIgMCAwIDEtMSAxLjczbC0uNDMuMjVhMiAyIDAgMCAxLTIgMGwtLjE1LS4wOGEyIDIgMCAwIDAtMi43My43M2wtLjIyLjM4YTIgMiAwIDAgMCAuNzMgMi43M2wuMTUuMWEyIDIgMCAwIDEgMSAxLjcydi41MWEyIDIgMCAwIDEtMSAxLjc0bC0uMTUuMDlhMiAyIDAgMCAwLS43MyAyLjczbC4yMi4zOGEyIDIgMCAwIDAgMi43My43M2wuMTUtLjA4YTIgMiAwIDAgMSAyIDBsLjQzLjI1YTIgMiAwIDAgMSAxIDEuNzNWMjBhMiAyIDAgMCAwIDIgMmguNDRhMiAyIDAgMCAwIDItMnYtLjE4YTIgMiAwIDAgMSAxLTEuNzNsLjQzLS4yNWEyIDIgMCAwIDEgMiAwbC4xNS4wOGEyIDIgMCAwIDAgMi43My0uNzNsLjIyLS4zOWEyIDIgMCAwIDAtLjczLTIuNzNsLS4xNS0uMDhhMiAyIDAgMCAxLTEtMS43NHYtLjVhMiAyIDAgMCAxIDEtMS43NGwuMTUtLjA5YTIgMiAwIDAgMCAuNzMtMi43M2wtLjIyLS4zOGEyIDIgMCAwIDAtMi43My0uNzNsLS4xNS4wOGEyIDIgMCAwIDEtMiAwbC0uNDMtLjI1YTIgMiAwIDAgMS0xLTEuNzNWNGEyIDIgMCAwIDAtMi0yeiIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjMiLz48L3N2Zz4=',
  'dollar-sign': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGxpbmUgeDE9IjEyIiB4Mj0iMTIiIHkxPSIyIiB5Mj0iMjIiLz48cGF0aCBkPSJNMTcgNUg5LjVhMy41IDMuNSAwIDAgMCAwIDdoNWEzLjUgMy41IDAgMCAxIDAgN0g2Ii8+PC9zdmc+',
  'credit-card': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjE0IiB4PSIyIiB5PSI1IiByeD0iMiIvPjxsaW5lIHgxPSIyIiB4Mj0iMjIiIHkxPSIxMCIgeTI9IjEwIi8+PC9zdmc+',
  'wallet': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTE5IDdWNGExIDEgMCAwIDAtMS0xSDVhMiAyIDAgMCAwIDAgNGgxNWExIDEgMCAwIDEgMSAxdjRoLTNhMiAyIDAgMCAwIDAgNGgzYTEgMSAwIDAgMCAxLTF2LTJhMSAxIDAgMCAwLTEtMSIvPjxwYXRoIGQ9Ik0zIDV2MTRhMiAyIDAgMCAwIDIgMmgxNWExIDEgMCAwIDAgMS0xdi00Ii8+PC9zdmc+',
  'coins': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iOCIgY3k9IjgiIHI9IjYiLz48cGF0aCBkPSJNMTguMDkgMTAuMzdBNiA2IDAgMSAxIDEwLjM0IDE4Ii8+PHBhdGggZD0iTTcgNmgxdjQiLz48bGluZSB4MT0iMTYuNzEiIHgyPSIxMy4yOSIgeTE9IjEzLjI5IiB5Mj0iMTYuNzEiLz48L3N2Zz4=',
  'plus-circle': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48bGluZSB4MT0iMTIiIHgyPSIxMiIgeTE9IjgiIHkyPSIxNiIvPjxsaW5lIHgxPSI4IiB4Mj0iMTYiIHkxPSIxMiIgeTI9IjEyIi8+PC9zdmc+',
  'search': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTEiIGN5PSIxMSIgcj0iOCIvPjxsaW5lIHgxPSIyMSIgeDI9IjE2LjY1IiB5MT0iMjEiIHkyPSIxNi42NSIvPjwvc3ZnPg==',
  'eye': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIgMTJzMy03IDEwLTcgMTAgNyAxMCA3LTMgNy0xMCA3LTEwLTctMTAtN1oiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIzIi8+PC9zdmc+',
  'download': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIxIDE1djRhMiAyIDAgMCAxLTIgMkg1YTIgMiAwIDAgMS0yLTJ2LTQiLz48cG9seWxpbmUgcG9pbnRzPSI3IDEwIDEyIDE1IDE3IDEwIi8+PGxpbmUgeDE9IjEyIiB4Mj0iMTIiIHkxPSIxNSIgeTI9IjMiLz48L3N2Zz4=',
  'upload': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIxIDE1djRhMiAyIDAgMCAxLTIgMkg1YTIgMiAwIDAgMS0yLTJ2LTQiLz48cG9seWxpbmUgcG9pbnRzPSIxNyA4IDEyIDMgNyA4Ii8+PGxpbmUgeDE9IjEyIiB4Mj0iMTIiIHkxPSIzIiB5Mj0iMTUiLz48L3N2Zz4=',
  'list': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGxpbmUgeDE9IjgiIHgyPSIyMSIgeTE9IjYiIHkyPSI2Ii8+PGxpbmUgeDE9IjgiIHgyPSIyMSIgeTE9IjEyIiB5Mj0iMTIiLz48bGluZSB4MT0iOCIgeDI9IjIxIiB5MT0iMTgiIHkyPSIxOCIvPjxsaW5lIHgxPSIzIiB4Mj0iMy4wMSIgeTE9IjYiIHkyPSI2Ii8+PGxpbmUgeDE9IjMiIHgyPSIzLjAxIiB5MT0iMTIiIHkyPSIxMiIvPjxsaW5lIHgxPSIzIiB4Mj0iMy4wMSIgeTE9IjE4IiB5Mj0iMTgiLz48L3N2Zz4=',
  'check': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiLz48L3N2Zz4=',
  'info': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJNMTIgMTZ2LTQiLz48cGF0aCBkPSJNMTIgOGguMDEiLz48L3N2Zz4=',
  'lightbulb': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTE1IDE0Yy4yLTEgLjctMS43IDEuNS0yLjUgMS0uOSAxLjUtMi4yIDEuNS0zLjVBNiA2IDAgMCAwIDYgOGMwIDEgLjIgMi4yIDEuNSAzLjUuNy43IDEuMyAxLjUgMS41IDIuNSIvPjxwYXRoIGQ9Ik05IDE4aDYiLz48cGF0aCBkPSJNMTAgMjJoNCIvPjwvc3ZnPg==',
  'map-pin': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIwIDEwYzAgNi04IDEyLTggMTJzLTgtNi04LTEyYTggOCAwIDAgMSAxNiAwWiIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTAiIHI9IjMiLz48L3N2Zz4=',
};

// 아이콘 렌더링 헬퍼: 원형 배경 + 중앙 아이콘
// name: ICON_SET 키, x/y/d: 위치·지름(인치), bgColor: 배경색(hex, # 포함 가능)
function pm_addIcon(s, name, x, y, d, bgColor) {
  const col = (bgColor||'').replace('#','') || 'FFFFFF';
  s.addShape('ellipse', { x, y, w: d, h: d,
    fill: { color: col }, line: { type: 'none' } });
  const iconData = ICON_SET[name] || ICON_SET['target'];
  const pad = d * 0.22;
  s.addImage({ data: iconData, x: x + pad, y: y + pad,
    w: d - pad * 2, h: d - pad * 2 });
}

// body 텍스트에서 [icon-name] prefix 추출 헬퍼
// "[compass] 1단계: 분석" → { icon: 'compass', text: '1단계: 분석' }
// 아이콘 없으면 → { icon: null, text: 원문 }
function parseIconItem(text) {
  if (!text) return { icon: null, text: text || '' };
  const m = String(text).match(/^\[([a-z][a-z0-9-]*)\]\s*(.*)/s);
  if (m && (ICON_SET[m[1]] || ICON_SET['target'])) return { icon: m[1], text: m[2] };
  return { icon: null, text: String(text) };
}

// ── _ff: string 또는 {F,FH,FD} 객체 모두 수용하는 backward-compat 헬퍼 ──
function _ff(fontsArg) {
  if (typeof fontsArg === 'string') return { F: fontsArg, FH: fontsArg, FD: fontsArg };
  return {
    F:  fontsArg.F  || '맑은 고딕',
    FH: fontsArg.FH || fontsArg.F || '맑은 고딕',
    FD: fontsArg.FD || fontsArg.FH || fontsArg.F || '맑은 고딕',
  };
}

// ════════════════════════════════════════════════════════
// PPTMON 인라인 함수 (pptmon_template_v2.js → ES Module 제거 버전)
// ════════════════════════════════════════════════════════
// 슬라이드 크기 상수 (모든 pm_add* 함수에서 공유)
const W = 13.3333, H = 7.5;

// M2: 공통 레이아웃 상수
const PM = {
  PAD: W * 0.04,               // 기본 패딩 (4%)
  PAD_SM: W * 0.036,           // 작은 패딩
  EYEBROW_H: 0.28,             // 아이브로우 필 높이
  EYEBROW_FS: 8.5,             // 아이브로우 폰트 크기
  EYEBROW_SP: 2,               // 아이브로우 문자 간격
  ACCENT_BAR_W: 0.055,         // 좌측 악센트 바 폭
  DIVIDER_W: 0.04,             // 패널 구분선 폭
  CARD_RADIUS: 0.16,           // 카드 모서리
  COPYRIGHT_FS: 7,             // 저작권 폰트 크기
  PAGENUM_FS: 9,               // 페이지 번호 폰트 크기
  SPLIT_IMG_RATIO: 0.42,       // split 이미지 패널 비율
  CARDS_IMG_RATIO: 0.40,       // cards 이미지 패널 비율
  OVERLAY_T: 32,               // 이미지 오버레이 transparency
};

// Phase 8: 카드 soft shadow — 비활성화 (PPTX 복구 오류 원인)
const PM_CARD_SHADOW = undefined;

// 공통 프레임: eyebrow pill + 타이틀 + full-width 구분선
function pm_addSlideFrame(s, C, fonts, title, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  s.background = { color: C.bg };
  // 우상단 대형 데코 원 (Glassmorphic 레퍼런스)
  s.addShape('ellipse', {
    x: W * 0.72, y: -H * 0.20, w: H * 0.82, h: H * 0.82,
    fill: { color: C.primary, transparency: 94 }, line: { type: 'none' }
  });
  // 좌 primary 수직 accent bar (브랜드 일관성 — PDF2 레퍼런스)
  s.addShape('rect', { x: 0, y: 0, w: PM.ACCENT_BAR_W, h: H, fill: { color: C.primary }, line: { type: 'none' } });

  // 본문 콘텐츠 시작 X와 동일하게 정렬 (eyebrow·타이틀·구분선 모두 같은 X)
  const aX = 0.533;
  const aW = W - aX - 0.28;   // 우측 여백 0.28"

  // ① eyebrow pill — 본문 좌측과 동일 X 정렬
  const ewH = 0.28;
  let titleY = 0.16;   // eyebrow 없을 때 타이틀 상단 여백
  if (eyebrow) {
    const ewStr = eyebrow.toUpperCase();
    // 한국어 등 비ASCII 문자는 2배 폭으로 환산
    const ewLen = ewStr.replace(/[^\x00-\xff]/g, 'xx').length;
    const ewW = Math.min(ewLen * 0.125 + 0.48, 5.0);
    // eyebrow pill (단색 — PptxGenJS gradient/overlay 호환 이슈로 단순화)
    s.addShape('roundRect', { x: aX, y: 0.12, w: ewW, h: ewH,
      fill: { color: C.eyebrowFill || C.primary }, line: { type: 'none' }, rectRadius: ewH / 2 });
    s.addText(ewStr, { x: aX, y: 0.12, w: ewW, h: ewH,
      fontSize: 10, bold: true, color: C.textOnPrimary, charSpacing: 1,
      align: 'center', valign: 'middle', fontFace: FH, wrap: false });
    titleY = 0.12 + ewH + 0.10;  // 0.50
  }

  // ② 타이틀 (eyebrow 바로 아래, 전체 폭) — wrap+shrinkText로 오버플로우 방지
  const titleFs = title.length > 22 ? 24 : title.length > 14 ? 28 : 32;
  // 긴 제목은 2줄 가능성 → 높이를 넉넉히 (divider 위치에 영향)
  const titleH = title.length > 28 ? 0.88 : title.length > 18 ? 0.72 : 0.58;
  // ── 두 가지 색 헤드라인 (Business Blue 레퍼런스 — 마지막 단어 accent) ──
  const _ttParts = title.trim().split(/\s+/);
  const _ttLast = _ttParts[_ttParts.length - 1] || '';
  const _twoTone = _ttParts.length >= 2 && _ttLast.replace(/[^\x00-\xff]/g,'xx').length <= 6;
  if (_twoTone) {
    s.addText([
      { text: _ttParts.slice(0, -1).join(' ') + ' ', options: { color: C.textPrimary, bold: true } },
      { text: _ttLast, options: { color: C.eyebrowFill || C.primary, bold: true } }
    ], {
      x: aX, y: titleY, w: aW, h: titleH,
      fontFace: FH, fontSize: titleFs,
      valign: 'middle', wrap: true, shrinkText: true });
  } else {
    s.addText(title, {
      x: aX, y: titleY, w: aW, h: titleH,
      fontFace: FH, fontSize: titleFs, bold: true, color: C.textPrimary,
      valign: 'middle', wrap: true, shrinkText: true });
  }

  // ③ full-width 타이틀 바 (G-1: Brandlogy 참고 — 얇은 primary 바 + 기존 구분선)
  const dividerY = titleY + titleH + 0.08;
  // primary 컬러 얇은 바 (전폭 시각적 앵커)
  // 전폭 primary 구분 바 (G-1: Brandlogy 참고)
  s.addShape('rect', { x: aX, y: dividerY, w: aW, h: 0.04,
    fill: { color: C.primary }, line: { type: 'none' } });
  return dividerY;
}

// ── 아이콘 박스 헬퍼: 라운드 테두리 박스 + primary 아이콘 원 내장 (Business Annual Report 스타일) ──
// boxSize에 비례한 라운드 코너로 전체 통일감 유지
function pm_addIconBox(s, C, fonts, x, y, boxSize, iconName, idx) {
  const {F, FH} = _ff(fonts);
  const bR = Math.min(boxSize * 0.18, 0.20);   // 크기 비례 라운드 — 통일 공식
  // 아이콘/번호 공통: primary 채운 roundRect (G-1: soft shadow)
  s.addShape('roundRect', { x, y, w: boxSize, h: boxSize,
    fill: { color: C.primary }, line: { type: 'none' }, rectRadius: bR,
    shadow: PM_CARD_SHADOW });
  if (iconName && ICON_SET[iconName]) {
    // 아이콘 직접 배치 (pm_addIcon 사용 안함 — ellipse 추가 방지)
    const pad = boxSize * 0.22;
    s.addImage({ data: ICON_SET[iconName], x: x + pad, y: y + pad,
      w: boxSize - pad * 2, h: boxSize - pad * 2 });
  } else {
    // 번호 fallback: 박스에 번호 직접 표시
    s.addText(String((idx || 0) + 1), { x, y, w: boxSize, h: boxSize,
      fontFace: FH, fontSize: Math.round(boxSize * 30), bold: true,
      color: C.textOnPrimary, align: 'center', valign: 'middle' });
  }
}

// ── Adaptive Cards: 아이템 수(n)에 따라 레이아웃 자동 선택 (Business Annual Report 레퍼런스) ──
// n=2 → 2열 대형 아이콘박스  n=3 → 3열  n=4 → 2×2 수평카드  n=5~6 → 2×3 그리드
// 모든 아이콘박스: 라운드 테두리 박스 통일 (사용자 선호)
function pm_addAdaptiveCards(s, C, fonts, title, items, eyebrow) {
  const {F, FH} = _ff(fonts);
  const N = Math.min(items.length, 6);
  if (N === 0) return;
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');

  const aX = 0.533, aW = W - aX - 0.28;
  const aY = divY + 0.22;
  const aH = H - aY - 0.55;  // 0.55" 하단 여백 (copyright 공간 확보)
  const GAP = 0.16;
  const CARD_R = 0.16;   // 카드 라운드 — 아이콘박스와 동일 계열

  // N별 레이아웃 설정
  const cols = N <= 3 ? N : (N === 4 ? 2 : 3);
  const rows = N <= 3 ? 1 : 2;
  const isHoriz = false;   // 수직 레이아웃 통일 (아이콘 상단, 텍스트 하단)
  const cardW = (aW - GAP * (cols - 1)) / cols;
  // 단일 행(n≤3)은 카드 높이 제한 — 텍스트 아래 여백 과다 방지
  const rawCardH = (aH - GAP * (rows - 1)) / rows;
  const cardH = rows === 1 ? Math.min(rawCardH, N <= 2 ? 4.80 : 3.60) : rawCardH;
  // 단일 행: 수직 중앙 정렬 (남은 공간을 상하 균등 배분), 복수 행: 0
  const cardOffsetY = rows === 1 ? Math.max(0, (aH - cardH) / 2) : 0;
  // 아이콘박스 크기 (N에 따라 점진적 축소)
  const boxSize = N <= 2 ? Math.min(cardW * 0.26, 1.02)
                : N === 3 ? Math.min(cardW * 0.32, 1.00)
                : N === 4 ? Math.min(cardH * 0.52, 0.62)
                : Math.min(cardW * 0.26, 0.54);

  // 아이콘 일관성: 하나라도 아이콘 없으면 전부 번호로 통일
  const _parsedItems = items.slice(0, cols * rows).map(it => parseIconItem(it));
  const _allHaveIcons = _parsedItems.every(p => p.icon && ICON_SET[p.icon]);

  items.slice(0, cols * rows).forEach((item, i) => {
    const col = i % cols, row = Math.floor(i / cols);
    const cx = aX + col * (cardW + GAP);
    const cy = aY + cardOffsetY + row * (cardH + GAP);

    // 텍스트 파싱
    const parsed = _parsedItems[i];
    // 혼용 방지: 전부 아이콘이 아니면 아이콘 무시
    if (!_allHaveIcons) parsed.icon = null;
    const ci = parsed.text.indexOf(':');
    const _rawHead = ci > 0 && ci <= 25 ? parsed.text.slice(0, ci).trim()
                   : parsed.text.slice(0, Math.min(20, parsed.text.length));
    // [icon-name] 접두사 잔류 방지 (parseIconItem fallback 안전망)
    const heading = _rawHead.replace(/^\[([a-z][a-z0-9-]*)\]\s*/i, '');
    const bodyTxt = ci > 0 && ci <= 25 ? parsed.text.slice(ci + 1).trim()
                  : parsed.text.length > 20 ? parsed.text.slice(20) : '';

    // 카드 배경 (흰 roundRect, G-1: soft shadow)
    s.addShape('roundRect', { x: cx, y: cy, w: cardW, h: cardH,
      fill: { color: 'FFFFFF' },
      line: { color: C.lineColor, width: 0.5 },
      rectRadius: CARD_R, shadow: PM_CARD_SHADOW });

    if (isHoriz) {
      // ── 수평 카드 (n=4): 아이콘박스 좌측 + 제목·본문 우측 ──
      const bY = cy + (cardH - boxSize) / 2;
      pm_addIconBox(s, C, fonts, cx + 0.18, bY, boxSize, parsed.icon, i);
      const tX = cx + 0.18 + boxSize + 0.18;
      const tW = cx + cardW - tX - 0.14;
      s.addText(heading, { x: tX, y: cy + 0.20, w: tW, h: 0.42,
        fontFace: FH, fontSize: 14, bold: true, color: C.primary,
        valign: 'middle', wrap: true, lineSpacingMultiple: 1.2 });
      s.addText(bodyTxt, { x: tX, y: cy + 0.66, w: tW, h: cardH - 0.74,
        fontFace: F, fontSize: 12, color: C.textSecondary,
        valign: 'top', wrap: true, lineSpacingMultiple: 1.35 });
    } else {
      // ── 수직 카드 (n=2/3/6): 아이콘박스 카드 내부 상단 ──
      const bX = cx + (cardW - boxSize) / 2;
      const bTopPad = N <= 3 ? 0.36 : 0.24;  // 카드 안쪽으로 충분히 (겹침 방지)
      pm_addIconBox(s, C, fonts, bX, cy + bTopPad, boxSize, parsed.icon, i);
      const tY = cy + bTopPad + boxSize + 0.20;
      const titleFs = N <= 2 ? 16 : N === 3 ? 17 : 13;
      const hlH    = N <= 3 ? 0.52 : 0.40;   // 17pt는 2줄 가능 → 높이 여유
      const bodyFs  = N <= 2 ? 13 : N === 3 ? 14 : 11;
      s.addText(heading, { x: cx + 0.18, y: tY, w: cardW - 0.36, h: hlH,
        fontFace: FH, fontSize: titleFs, bold: true, color: C.primary,
        align: 'left', valign: 'middle', wrap: true, shrinkText: true });
      s.addText(bodyTxt, { x: cx + 0.18, y: tY + hlH + 0.14, w: cardW - 0.36, h: cardH - (tY - cy) - hlH - 0.38,
        fontFace: F, fontSize: bodyFs, color: C.textSecondary,
        align: 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.40 });
    }
  });
}

// 카드 내용 (v10.9 플랫 디자인): 흰 roundRect + 상단 primary 헤더 바 + 아이콘 + ↗ 배지
// icon: ICON_SET 키 문자열 (있으면 상단 좌측에 아이콘 원형 렌더링, 없으면 번호 pill)
function pm_addContentCard(s, C, fonts, x, y, w, h, heading, bodyText, icon, idx) {
  const {F, FH, FD} = _ff(fonts);
  const r = 0.16;
  // 카드 본체 (G-1: soft shadow)
  s.addShape('roundRect', { x, y, w, h,
    fill: { color: 'FFFFFF' },
    line: { color: C.lineColor, width: 0.5 }, rectRadius: r,
    shadow: PM_CARD_SHADOW });
  // 상단 primary 액센트 바 (두꺼운)
  s.addShape('roundRect', { x, y, w, h: 0.09,
    fill: { color: C.primary }, line: { type: 'none' }, rectRadius: r * 0.5 });

  // 아이콘 or 번호 배지
  const iD = 0.38;
  const iX = x + 0.14, iY = y + 0.18;
  if (icon && ICON_SET[icon]) {
    pm_addIcon(s, icon, iX, iY, iD, C.primary);
  } else if (idx !== undefined) {
    // 번호 pill (01/02/03)
    s.addShape('roundRect', { x: iX, y: iY, w: iD, h: iD * 0.70,
      fill: { color: C.primary }, line: { type: 'none' }, rectRadius: iD * 0.35 });
    s.addText(String((idx||0) + 1).padStart(2,'0'), {
      x: iX, y: iY, w: iD, h: iD * 0.70,
      fontFace: FH, fontSize: 8.5, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle' });
  }

  // 헤딩 (아이콘 우측 or 아이콘 없으면 상단)
  const hasIcon = !!(icon || idx !== undefined);
  const headY = hasIcon ? iY : y + 0.14;
  const headX = hasIcon ? iX + iD + 0.10 : x + 0.12;
  const headW = hasIcon ? w - (headX - x) - 0.12 : w - 0.24;
  s.addText(heading || '', {
    x: headX, y: headY, w: headW, h: 0.56,
    fontFace: FH, fontSize: 12.5, bold: true, color: C.primary,
    valign: 'middle', wrap: true, lineSpacingMultiple: 1.2 });

  // 본문
  const bodyY = y + (hasIcon ? iY - y + iD * 0.70 + 0.16 : 0.80);
  s.addText(bodyText || '', {
    x: x + 0.12, y: bodyY, w: w - 0.24, h: h - (bodyY - y) - 0.30,
    fontFace: F, fontSize: 12, color: C.textSecondary,
    valign: 'top', wrap: true, lineSpacingMultiple: 1.35 });

  // ↗ 배지 (우하단)
  const bD = 0.24;
  s.addShape('ellipse', { x: x + w - bD - 0.10, y: y + h - bD - 0.10, w: bD, h: bD,
    fill: { color: C.primary }, line: { type: 'none' } });
  s.addText('↗', { x: x + w - bD - 0.10, y: y + h - bD - 0.10, w: bD, h: bD,
    fontFace: F, fontSize: 7.5, bold: true, color: C.textOnPrimary,
    align: 'center', valign: 'middle' });
}

// S26 지그재그 타임라인 (pptmon_template_v2.js § 8 — 원본 좌표 기준)
function pm_addZigzagTimeline(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  // 원본 S26 상수
  const circleSize   = 1.257;
  const circleXs     = [2.895, 4.398, 5.919, 7.415, 8.933];
  const topCircleY   = 2.677, topTextY    = 1.312;
  const bottomCircleY= 4.245, bottomTextY = 5.715;
  const diamondY     = 3.023;
  const cardW = 2.768, cardH = 1.212;
  items.slice(0, 5).forEach((item, idx) => {
    const isTop = idx % 2 === 1;           // 원본 기준: 1번째 아이템은 하단
    const cx = circleXs[idx];
    const cy = isTop ? topCircleY : bottomCircleY;
    // 원
    s.addShape('ellipse', { x: cx, y: cy, w: circleSize, h: circleSize,
      fill: { color: C.primary }, line: { type: 'none' } });
    s.addText(item.year || String(idx + 1), { x: cx, y: cy,
      w: circleSize, h: circleSize, fontFace: F, fontSize: 18,
      color: C.textOnPrimary, bold: true,
      valign: 'middle', align: 'center' });
    // 다이아몬드 연결자
    if (idx < items.length - 1 && idx < 4) {
      const midX = (cx + circleXs[idx + 1]) / 2 - 0.3;
      s.addShape('diamond', { x: midX, y: diamondY + 0.3, w: 0.6, h: 0.6,
        fill: { color: C.accentLight }, line: { type: 'none' } });
    }
    // 텍스트 카드 (textX: cx - cardW/2 + circleSize/2)
    const textY = isTop ? topTextY : bottomTextY;
    const textX = cx - cardW / 2 + circleSize / 2;
    pm_addContentCard(s, C, fonts, textX, textY, cardW, cardH,
      item.heading, item.body);
  });
}

// S28 4-스텝 프로세스 (pptmon_template_v2.js § 10 — 원본 좌표 기준)
function pm_add4StepProcess(s, C, fonts, title, steps, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  // 원본 S28 상수
  const circleSize = 2.486, circleY = 2.50;
  const circleXs   = [0.653, 3.597, 6.694, 9.806];
  const triW = 1.069, triH = 0.667;
  const triXs = [3.083, 6.181, 9.292], triY = 3.41;
  const cardW = 2.764, cardH = 1.25,  cardY = 5.15;
  const cardXs = [0.500, 3.444, 6.556, 9.653];
  steps.slice(0, 4).forEach((step, idx) => {
    // 원 + 번호/라벨
    s.addShape('ellipse', { x: circleXs[idx], y: circleY,
      w: circleSize, h: circleSize,
      fill: { color: C.primary }, line: { type: 'none' } });
    s.addText([
      { text: step.number || String(idx + 1).padStart(2, '0'),
        options: { fontSize: 32, bold: true, color: C.textOnPrimary,
          fontFace: FD, breakLine: true }},
      { text: step.label || '',
        options: { fontSize: 12, color: C.textOnPrimary, fontFace: F }},
    ], { x: circleXs[idx], y: circleY, w: circleSize, h: circleSize,
         valign: 'middle', align: 'center' });
    // 연결 삼각형
    if (idx < 3) {
      s.addShape('triangle', { x: triXs[idx], y: triY,
        w: triW, h: triH,
        fill: { color: C.accentLight }, line: { type: 'none' }, rotate: 90 });
    }
    // 카드
    pm_addContentCard(s, C, fonts, cardXs[idx], cardY, cardW, cardH,
      step.heading, step.body);
  });
}

// S29 방사형 다이어그램 (pptmon_template_v2.js § 11 — 원본 좌표 기준)
function pm_addRadialDiagram(s, C, fonts, title, centerLabel, cards, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  // 원본 S29 상수
  const cc = { x: 4.319, y: 1.903, w: 4.472, h: 4.472 };
  const positions = [
    { x: 7.083, y: 1.111, w: 4.222, h: 1.111 },
    { x: 9.583, y: 3.792, w: 3.069, h: 1.361 },
    { x: 0.319, y: 3.556, w: 3.069, h: 1.361 },
    { x: 2.042, y: 5.736, w: 3.389, h: 1.361 },
  ];
  // 중앙 솔리드 원 중심점
  const solidCX = 5.705 + 1.7 / 2;  // 6.555
  const solidCY = 3.289 + 1.7 / 2;  // 4.139
  // 중앙 점선 원 (원본과 동일)
  s.addShape('ellipse', { x: cc.x, y: cc.y, w: cc.w, h: cc.h,
    line: { color: C.accentLight, width: 1.0, dashType: 'dash' },
    fill: { type: 'none' } });
  // 카드 중심→솔리드 원 연결선 (PptxGenJS는 음수 w/h 지원 안 함 → 최소 좌표로 정규화)
  positions.slice(0, Math.min(cards.length, 4)).forEach((pos) => {
    const cardCX = pos.x + pos.w / 2;
    const cardCY = pos.y + pos.h / 2;
    const lx = Math.min(solidCX, cardCX);
    const ly = Math.min(solidCY, cardCY);
    const lw = Math.abs(cardCX - solidCX);
    const lh = Math.abs(cardCY - solidCY);
    // 방향 반전 여부 (선이 우하→좌상, 좌하→우상 등인 경우 flip 설정)
    const flipH = cardCX < solidCX;
    const flipV = cardCY < solidCY;
    s.addShape('line', { x: lx, y: ly, w: lw || 0.01, h: lh || 0.01,
      flipH, flipV,
      line: { color: C.accentLight, width: 1.0, dashType: 'sysDot' } });
  });
  // 중앙 솔리드 원 + 라벨
  if (centerLabel) {
    s.addShape('ellipse', { x: 5.705, y: 3.289, w: 1.7, h: 1.7,
      fill: { color: C.primary }, line: { type: 'none' } });
    s.addText(centerLabel, { x: 5.705, y: 3.289, w: 1.7, h: 1.7,
      fontFace: FH, fontSize: 11, bold: true,
      color: C.textOnPrimary, align: 'center', valign: 'middle', wrap: true });
  }
  // 4 카드
  cards.slice(0, 4).forEach((card, idx) => {
    const pos = positions[idx];
    pm_addContentCard(s, C, fonts, pos.x, pos.y, pos.w, pos.h,
      card.heading, card.body);
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW-F: KPI Cards — 4개 대형 숫자 카드 (이미지 불필요)
// 용도: 핵심 지표/성과 숫자를 강조할 때
// ─────────────────────────────────────────────────────────────────
function pm_addKPICards(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 4);
  if (N === 0) return;
  const aX = 0.533, aY = divY + 0.28, aW = W - aX - 0.28;
  const aH = Math.min(H - aY - 0.55, 4.40);  // 0.55" 하단 여백 (copyright 공간 확보)
  const gap = 0.18;
  const cW = (aW - gap * (N - 1)) / N;
  const cH = aH, r = 0.14;
  const cardFills = [C.primary, C.accentDark,
                     _pm_hslShift(C.primary, -0.12, 0.05), _pm_hslShift(C.primary, 0.20, -0.10)];
  // 4번째 카드가 너무 밝으면 deep shade 사용 (회색 폴백 제거)
  const lastFill = _pm_light(cardFills[3]) ? C.accentDark : cardFills[3];

  items.slice(0, N).forEach((item, idx) => {
    const cx = aX + idx * (cW + gap);
    const fill = idx === 0 ? C.primary : idx === 1 ? C.accentDark :
                 idx === 2 ? _pm_bright(C.primary, -0.12) : lastFill;
    const isLight = _pm_light(fill);
    const txtClr = isLight ? C.textPrimary : C.textOnPrimary;
    const subClr = isLight ? C.textSecondary : _pm_bright(fill, 0.50);

    // 카드 배경
    s.addShape('roundRect', { x: cx, y: aY, w: cW, h: cH,
      fill: { color: fill }, line: { type: 'none' }, rectRadius: r });

    // ① 라벨 chip (Glassmorphic 레퍼런스 — isLight 여부에 따라 색상 자동 조정)
    const _chipText = (item.label || item.body || '').toUpperCase().slice(0, 20);
    const _chipW = Math.min(_chipText.length * 0.095 + 0.45, cW - 0.30);
    const _chipBg = isLight ? C.primary : 'FFFFFF';
    const _chipBgT = isLight ? 85 : 10;
    const _chipTxtClr = isLight ? C.primary : C.primary;
    s.addShape('roundRect', {
      x: cx + 0.15, y: aY + 0.18, w: _chipW, h: 0.28,
      fill: { color: _chipBg, transparency: _chipBgT },
      line: { color: isLight ? C.primary : C.accentLight, width: 0.75 }, rectRadius: 0.14 });
    s.addText(_chipText, {
      x: cx + 0.15, y: aY + 0.18, w: _chipW, h: 0.28,
      fontFace: F, fontSize: 9, bold: true, color: _chipTxtClr,
      charSpacing: 0.5, align: 'center', valign: 'middle' });

    // 대형 KPI 값 (chip 아래) — 52pt로 임팩트 증가
    s.addText(item.value || item.heading || '', {
      x: cx + 0.18, y: aY + 0.66, w: cW - 0.36, h: 2.10,
      fontFace: FD, fontSize: 52, bold: true, color: txtClr,
      align: 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.05 });

    // 라벨 설명 텍스트 (body만 사용 — label은 상단 chip에 이미 표시됨)
    const _descTxt = (item.body || '').trim();
    if (_descTxt) {
      s.addText(_descTxt, {
        x: cx + 0.18, y: aY + 2.86, w: cW - 0.36, h: cH - 3.10,
        fontFace: F, fontSize: 16, color: subClr,
        align: 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.40 });
    }

    // ↗ 배지 or 아이콘 (우상단, 크기 증가)
    const bD = item.icon ? 0.52 : 0.50;
    const bX = cx + cW - bD - 0.14, bY = aY + 0.14;
    if (item.icon) {
      pm_addIcon(s, item.icon, bX, bY, bD,
        isLight ? C.primary : 'FFFFFF');
    } else {
      s.addShape('ellipse', { x: bX, y: bY, w: bD, h: bD,
        fill: { color: isLight ? C.primary : 'FFFFFF', transparency: isLight ? 0 : 55 },
        line: { type: 'none' } });
      s.addText('↗', { x: bX, y: bY, w: bD, h: bD,
        fontFace: FD, fontSize: 17, bold: true,
        color: isLight ? C.textOnPrimary : txtClr,
        align: 'center', valign: 'middle' });
    }
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW-G: Timeline Bars — 연도별 수평 바 타임라인 (이미지 불필요)
// 용도: 연도/단계별 진행 현황이나 성장 과정을 보여줄 때
// ─────────────────────────────────────────────────────────────────
function pm_addTimelineBars(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 6);
  if (N === 0) return;
  const labelX = 0.533, barX = 2.10, barEndX = 12.50;
  const startY = divY + 1.51, totalH = 4.40;
  const rowH = totalH / N;
  const maxBarW = barEndX - barX;

  items.slice(0, N).forEach((item, idx) => {
    const ry = startY + idx * rowH;
    const isHighlight = item.highlight === true || idx === N - 1;
    const pct = item.percent ? Math.min(item.percent / 100, 1)
                             : (idx + 1) / N;
    const barH = Math.min(rowH * 0.46, 0.55);
    const barY = ry + (rowH - barH) / 2;
    const barW = maxBarW * pct;

    // 연도/라벨 텍스트
    s.addText(item.year || item.label || String(2020 + idx), {
      x: labelX, y: barY, w: 1.42, h: barH,
      fontFace: F, fontSize: 14, bold: isHighlight,
      color: isHighlight ? C.primary : C.textMuted,
      align: 'right', valign: 'middle' });

    // 배경 바 (전체 폭 회색)
    s.addShape('roundRect', { x: barX, y: barY, w: maxBarW, h: barH,
      fill: { color: C.lineColor }, line: { type: 'none' },
      rectRadius: barH / 2 });

    // 활성 바
    s.addShape('roundRect', { x: barX, y: barY, w: Math.max(barW, 0.15), h: barH,
      fill: { color: isHighlight ? C.primary : 'AAAAAA' },
      line: { type: 'none' }, rectRadius: barH / 2 });

    // 바 오른쪽 텍스트 (item body)
    if (item.body) {
      const remX = barX + barW + 0.15;
      const remW = barEndX - remX - 0.1;
      if (remW > 0.5) {
        s.addText(item.body, {
          x: remX, y: barY, w: Math.min(remW, 4.0), h: barH,
          fontFace: F, fontSize: 10.5, color: C.textSecondary,
          valign: 'middle', wrap: false });
      }
    }
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW-H: Ruled List — 수평 구분선 목록 (이미지 불필요)
// 용도: 원칙/가이드라인/정책 등 항목을 깔끔하게 나열할 때
// ─────────────────────────────────────────────────────────────────
function pm_addRuledList(s, C, fonts, title, items, eyebrow, sub) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 5);
  if (N === 0) return;
  const aX = 0.533, aW = 12.267;

  // 서브헤드라인: 구분선 바로 아래 표시 (공백 채움)
  let aY = divY + 0.40;
  if (sub) {
    s.addText(sub, { x: aX, y: divY + 0.16, w: aW, h: 0.44,
      fontFace: F, fontSize: 14, italic: false, color: C.textSecondary,
      valign: 'middle', wrap: true, lineSpacingMultiple: 1.2 });
    aY = divY + 0.68;
  }

  const rowH = (6.95 - aY) / N;  // 6.95" 기준 (copyright y=7.1" 위에 0.15" 여백)

  items.slice(0, N).forEach((item, idx) => {
    const ry = aY + idx * rowH;

    // 짝수 행 교차 배경 (Business Blue 레퍼런스)
    if (idx % 2 === 0) {
      s.addShape('rect', {
        x: aX - 0.05, y: ry - rowH * 0.05, w: aW + 0.10, h: rowH * 1.05,
        fill: { color: C.primary, transparency: 95 }, line: { type: 'none' }
      });
    }
    // 상단 구분선 (첫 항목 포함)
    s.addShape('line', { x: aX, y: ry, w: aW, h: 0,
      line: { color: C.lineColor, width: 0.5 } });

    // Pill 레이블 (번호 배지)
    const pillW = 0.62, pillH = 0.32;
    const pillY = ry + (rowH - pillH) / 2;
    s.addShape('roundRect', { x: aX, y: pillY, w: pillW, h: pillH,
      fill: { color: C.primary }, line: { type: 'none' }, rectRadius: pillH / 2 });
    s.addText(String(idx + 1).padStart(2, '0'), {
      x: aX, y: pillY, w: pillW, h: pillH,
      fontFace: F, fontSize: 9, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle' });

    // 제목 (굵게) — body 없으면 전체 폭 사용
    const titleX = aX + pillW + 0.18;
    const hasBody = !!(item.body || '').trim();
    const titleW = hasBody ? 4.20 : (aW - pillW - 0.54);
    s.addText(item.heading || '', {
      x: titleX, y: ry + 0.06, w: titleW, h: rowH - 0.10,
      fontFace: FH, fontSize: 15, bold: true, color: C.textPrimary,
      valign: 'middle', wrap: true, lineSpacingMultiple: 1.25 });

    // 본문 (우측) — body 있을 때만
    if (hasBody) {
      s.addText(item.body, {
        x: titleX + titleW + 0.18, y: ry + 0.06,
        w: aW - pillW - titleW - 0.54, h: rowH - 0.10,
        fontFace: F, fontSize: 12, color: C.textSecondary,
        valign: 'middle', wrap: true, lineSpacingMultiple: 1.3 });
    }
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW: Pull Quote — 풀스크린 인용구 (대형 발언·인사이트 강조)
// 용도: 고객 증언, 핵심 인사이트, 임팩트 있는 한 문장
// ─────────────────────────────────────────────────────────────────
function pm_addPullQuote(s, C, fonts, quote, attribution, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  // 배경: primary 컬러 풀스크린
  s.background = { color: C.primary };

  // 상단 얇은 액센트 바 (대비)
  s.addShape('rect', { x: 0, y: 0, w: W, h: 0.06,
    fill: { color: 'FFFFFF', transparency: 70 }, line: { type: 'none' } });

  // 장식용 대형 따옴표 (좌측 반투명)
  s.addText('\u201C', {
    x: -0.2, y: -0.6, w: 3.5, h: 3.5,
    fontFace: F, fontSize: 260, bold: true,
    color: 'FFFFFF', valign: 'top', align: 'left',
    transparency: 85 });

  // 핵심 텍스트 (eyebrow가 있으면 상단 pill)
  if (eyebrow) {
    const ewStr = eyebrow.toUpperCase();
    const ewW = Math.min(ewStr.length * 0.13 + 0.50, 3.5), ewH = 0.30;
    s.addShape('roundRect', { x: W * 0.09, y: H * 0.10, w: ewW, h: ewH,
      fill: { color: 'FFFFFF', transparency: 70 }, line: { type: 'none' }, rectRadius: ewH / 2 });
    s.addText(ewStr, { x: W * 0.09, y: H * 0.10, w: ewW, h: ewH,
      fontSize: 9, bold: true, color: 'FFFFFF', charSpacing: 2,
      align: 'center', valign: 'middle', fontFace: F });
  }

  // 인용 텍스트 (중앙 배치, 길이에 따라 font size 동적 조절)
  const qLen = (quote || '').length;
  const qFs = qLen > 120 ? 22 : qLen > 80 ? 26 : qLen > 50 ? 32 : 38;
  const qY = eyebrow ? H * 0.20 : H * 0.14;
  s.addText(`\u201C${quote}\u201D`, {
    x: W * 0.09, y: qY, w: W * 0.82, h: H * 0.62,
    fontFace: FD, fontSize: qFs, bold: true, color: 'FFFFFF',
    wrap: true, align: 'left', valign: 'middle',
    lineSpacingMultiple: 1.35 });

  // 하단 구분선 + 출처
  s.addShape('rect', { x: W * 0.09, y: H * 0.83, w: W * 0.15, h: 0.04,
    fill: { color: 'FFFFFF', transparency: 55 }, line: { type: 'none' } });
  if (attribution) {
    s.addText(`— ${attribution}`, {
      x: W * 0.09, y: H * 0.87, w: W * 0.82, h: H * 0.07,
      fontFace: F, fontSize: 12, color: 'FFFFFF',
      align: 'left', valign: 'top' });
  }
}

// ─────────────────────────────────────────────────────────────────
// NEW: Big Statement — 임팩트 문장 (텍스트+컬러 블록으로 꽉 찬 느낌)
// 용도: 핵심 주장 선언, 섹션 전환, 단일 큰 인사이트
// ─────────────────────────────────────────────────────────────────
function pm_addBigStatement(s, C, fonts, headline, subline, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  s.background = { color: 'FFFFFF' };

  // 우측 컬러 패널 (40%) — 공간을 채우는 핵심
  const panelX = W * 0.60;
  s.addShape('rect', { x: panelX, y: 0, w: W - panelX, h: H,
    fill: { color: C.primary }, line: { type: 'none' } });

  // 우측 패널 위 장식 원 (semi-transparent)
  s.addShape('ellipse', { x: panelX + (W - panelX) * 0.1, y: -H * 0.15,
    w: (W - panelX) * 1.0, h: (W - panelX) * 1.0,
    fill: { color: 'FFFFFF', transparency: 90 }, line: { type: 'none' } });

  // 좌측 수직 액센트 바
  s.addShape('rect', { x: W * 0.06, y: H * 0.15, w: W * 0.005, h: H * 0.70,
    fill: { color: C.primary }, line: { type: 'none' } });

  // eyebrow pill (좌측)
  if (eyebrow) {
    const ewStr = eyebrow.toUpperCase();
    const ewW = Math.min(ewStr.length * 0.13 + 0.50, 5.5), ewH = 0.30;
    s.addShape('roundRect', { x: W * 0.09, y: H * 0.15, w: ewW, h: ewH,
      fill: { color: C.primary }, line: { type: 'none' }, rectRadius: ewH / 2 });
    s.addText(ewStr, { x: W * 0.09, y: H * 0.15, w: ewW, h: ewH,
      fontSize: 9, bold: true, color: C.textOnPrimary, charSpacing: 2,
      align: 'center', valign: 'middle', fontFace: F });
  }

  // 대형 헤드라인 (좌측 55% 영역)
  const hlLen = (headline || '').length;
  const hlFs = hlLen > 60 ? 28 : hlLen > 40 ? 34 : hlLen > 24 ? 40 : 48;
  const hlY = eyebrow ? H * 0.25 : H * 0.18;
  s.addText(headline, {
    x: W * 0.09, y: hlY, w: W * 0.50, h: H * 0.55,
    fontFace: FD, fontSize: hlFs, bold: true, color: C.textPrimary,
    wrap: true, align: 'left', valign: 'middle',
    lineSpacingMultiple: 1.25 });

  // 서브라인 (primary 컬러 강조)
  if (subline) {
    s.addText(subline, {
      x: W * 0.09, y: H * 0.78, w: W * 0.50, h: H * 0.12,
      fontFace: F, fontSize: 15, color: C.primary,
      wrap: true, align: 'left', valign: 'top',
      lineSpacingMultiple: 1.3 });
  }

  // 우측 패널: 대형 장식 텍스트 (슬라이드 번호 or 기호)
  s.addText('\u2192', {
    x: panelX, y: 0, w: W - panelX, h: H,
    fontFace: F, fontSize: 120, bold: true, color: 'FFFFFF',
    align: 'center', valign: 'middle', transparency: 20 });
}

// ─────────────────────────────────────────────────────────────────
// NEW: Two Column Text — 좌 제목 + 우 목록 (텍스트 전용 2열)
// 용도: 어젠다, 목표, 이슈+해결, 요약 (이미지 없이 텍스트로 꽉 채움)
// ─────────────────────────────────────────────────────────────────
function pm_addTwoColText(s, C, fonts, title, items, eyebrow, sub) {
  const {F, FH, FD} = _ff(fonts);
  s.background = { color: 'FFFFFF' };

  // 액센트 라인 (상단)
  s.addShape('rect', { x: 0, y: 0, w: W, h: 0.06,
    fill: { color: C.primary }, line: { type: 'none' } });

  // 좌측 컬러 패널 (35%)
  const leftW = W * 0.36;
  s.addShape('rect', { x: 0, y: 0, w: leftW, h: H,
    fill: { color: C.primary }, line: { type: 'none' } });

  // 좌 패널: eyebrow (반투명 white pill)
  if (eyebrow) {
    const ewStr = eyebrow.toUpperCase();
    const ewW = Math.min(ewStr.length * 0.12 + 0.44, leftW * 0.85), ewH = 0.28;
    s.addShape('roundRect', { x: W * 0.05, y: H * 0.10, w: ewW, h: ewH,
      fill: { color: 'FFFFFF', transparency: 72 }, line: { type: 'none' }, rectRadius: ewH / 2 });
    s.addText(ewStr, { x: W * 0.05, y: H * 0.10, w: ewW, h: ewH,
      fontSize: 9, bold: true, color: 'FFFFFF', charSpacing: 2,
      align: 'center', valign: 'middle', fontFace: F });
  }

  // 좌 패널: 대형 제목 (흰색)
  const titleY = eyebrow ? H * 0.22 : H * 0.15;
  const titleFs = title.length > 20 ? 26 : title.length > 14 ? 32 : 38;
  s.addText(title, {
    x: W * 0.05, y: titleY, w: leftW - W * 0.07, h: H * 0.50,
    fontFace: FH, fontSize: titleFs, bold: true, color: 'FFFFFF',
    wrap: true, align: 'left', valign: 'middle',
    lineSpacingMultiple: 1.2 });

  // 좌 패널: sub (흰색 반투명)
  if (sub) {
    s.addText(sub, {
      x: W * 0.05, y: H * 0.75, w: leftW - W * 0.07, h: H * 0.18,
      fontFace: F, fontSize: 12, color: 'FFFFFF',
      wrap: true, align: 'left', valign: 'top',
      lineSpacingMultiple: 1.3, transparency: 25 });
  }

  // 우측 목록 영역
  const rX = leftW + W * 0.04;
  const rW = W - rX - W * 0.04;
  const N = Math.min(items.length, 6);
  if (N === 0) return;
  const rowH = (H * 0.86) / N;
  const listY = H * 0.07;

  items.slice(0, N).forEach((item, idx) => {
    const ry = listY + idx * rowH;

    // 구분선 (첫 항목 포함)
    s.addShape('line', { x: rX, y: ry, w: rW, h: 0,
      line: { color: C.lineColor, width: 0.6 } });

    // 번호 배지
    const bdW = 0.58, bdH = 0.28;
    const bdY = ry + (rowH - bdH) / 2;
    s.addShape('roundRect', { x: rX, y: bdY, w: bdW, h: bdH,
      fill: { color: C.primary }, line: { type: 'none' }, rectRadius: bdH / 2 });
    s.addText(String(idx + 1).padStart(2, '0'), {
      x: rX, y: bdY, w: bdW, h: bdH,
      fontFace: F, fontSize: 9, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle' });

    // 제목 (굵게)
    const hX = rX + bdW + 0.16;
    const hW = rW * 0.38;
    s.addText(item.heading || '', {
      x: hX, y: ry + 0.05, w: hW, h: rowH - 0.08,
      fontFace: F, fontSize: 16, bold: true, color: C.textPrimary,
      valign: 'middle', wrap: true, lineSpacingMultiple: 1.2 });

    // 설명 (우측)
    s.addText(item.body || '', {
      x: hX + hW + 0.14, y: ry + 0.05,
      w: rW - bdW - hW - 0.34, h: rowH - 0.08,
      fontFace: F, fontSize: 14, color: C.textSecondary,
      valign: 'middle', wrap: true, lineSpacingMultiple: 1.3 });
  });

  // 마지막 구분선
  s.addShape('line', { x: rX, y: listY + N * rowH, w: rW, h: 0,
    line: { color: C.lineColor, width: 0.6 } });
}

// ─────────────────────────────────────────────────────────────────
// Market Circles: 크기 차등 원 3개 — TAM/SAM/SOM (Business Blue 레퍼런스)
// ─────────────────────────────────────────────────────────────────
function pm_addMarketCircles(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');

  const N = Math.min(items.length, 3);
  if (N === 0) return;

  // 원 3개: 크기 비율 (large / medium / small)
  const ratios = [1.0, 0.72, 0.50];
  const maxD = Math.min(H - divY - 0.40, 3.80);
  const fills = [C.primary, C.accentLight, 'FFFFFF'];
  const textColors = [C.textOnPrimary, C.textOnAccentLight, C.primary];
  const borderColors = [null, null, C.primary];

  // 원들을 오른쪽 절반에 배치
  const circArea = W * 0.52;
  const circX0 = W * 0.26;
  const circY0 = divY + 0.28;

  // 3개 원 가로 배치 (겹치지 않게 간격)
  const totalD = items.slice(0, N).reduce((s, _, i) => s + maxD * ratios[i], 0);
  const gapBetween = (circArea - totalD) / Math.max(N - 1, 1);
  let cx = circX0;

  items.slice(0, N).forEach((item, i) => {
    const d = maxD * ratios[i];
    const r = d / 2;
    const cy = circY0 + (maxD - d) / 2;  // 하단 정렬

    // 원
    const shapeOpts = {
      x: cx, y: cy, w: d, h: d,
      fill: { color: fills[i] },
      line: borderColors[i] ? { color: borderColors[i], width: 1.5 } : { type: 'none' }
    };
    s.addShape('ellipse', shapeOpts);

    // 원 안의 숫자
    const raw = typeof item === 'object' ? (item.heading || '') : String(item || '');
    const colon = raw.indexOf(':');
    const numText = colon > 0 ? raw.slice(0, colon).trim() : raw;
    const lblText = colon > 0 ? raw.slice(colon + 1).trim() : '';

    const numFs = numText.length > 8 ? 14 : numText.length > 5 ? 16 : 20;
    s.addText(numText, {
      x: cx, y: cy + d * 0.25, w: d, h: d * 0.32,
      fontFace: FD, fontSize: numFs, bold: true,
      color: textColors[i], align: 'center', valign: 'middle' });
    if (lblText) {
      s.addText(lblText, {
        x: cx - 0.10, y: cy + d * 0.56, w: d + 0.20, h: d * 0.22,
        fontFace: F, fontSize: 8, color: textColors[i],
        align: 'center', valign: 'top', wrap: true });
    }

    cx += d + gapBetween;
  });

  // 우측 설명 텍스트 리스트
  const listX = W * 0.80, listW = W * 0.16;
  let listY = divY + 0.40;
  items.slice(0, N).forEach((item, i) => {
    const raw = typeof item === 'object' ? (item.heading || '') : String(item || '');
    const colon = raw.indexOf(':');
    const numText = colon > 0 ? raw.slice(0, colon).trim() : raw;
    const lblText = colon > 0 ? raw.slice(colon + 1).trim() : '';

    s.addShape('ellipse', { x: listX - 0.20, y: listY + 0.02, w: 0.14, h: 0.14,
      fill: { color: fills[i] }, line: { type: 'none' } });
    s.addText(numText, {
      x: listX, y: listY, w: listW, h: 0.22,
      fontFace: FH, fontSize: 10, bold: true, color: C.textPrimary });
    if (lblText) {
      s.addText(lblText, {
        x: listX, y: listY + 0.22, w: listW, h: 0.30,
        fontFace: F, fontSize: 8.5, color: C.textSecondary, wrap: true });
    }
    listY += 0.64;
  });
}

// ─────────────────────────────────────────────────────────────────
// Process Cards: numbered_process 변형 — 상단 컬러 밴드 카드 스타일
// ─────────────────────────────────────────────────────────────────
function pm_addProcessCards(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 5);
  if (N === 0) return;

  const aX = 0.28, aW = W - aX - 0.22;
  const gap = N <= 4 ? 0.18 : 0.12;
  const cardW = (aW - gap * (N - 1)) / N;
  const cardY = divY + 0.18;
  const cardH = H - cardY - 0.55;
  const bandH = cardH * 0.34;
  const r = 0.12;

  items.slice(0, N).forEach((item, i) => {
    const cx = aX + i * (cardW + gap);

    // card white background (G-1: soft shadow)
    s.addShape('roundRect', { x: cx, y: cardY, w: cardW, h: cardH,
      fill: { color: 'FFFFFF' },
      line: { color: 'E8E8F0', width: 0.5 },
      rectRadius: r, shadow: PM_CARD_SHADOW });

    // colored top band
    s.addShape('roundRect', { x: cx, y: cardY, w: cardW, h: bandH,
      fill: { color: C.primary }, line: { type: 'none' }, rectRadius: r });
    // cover bottom corners of band (to make only top rounded)
    s.addShape('rect', { x: cx, y: cardY + bandH - r, w: cardW, h: r,
      fill: { color: C.primary }, line: { type: 'none' } });

    // step number (single, larger)
    const bgNumStr = String(i + 1).padStart(2, '0');
    const _pcNumFs = N <= 3 ? 50 : N <= 4 ? 44 : 36;
    s.addText(bgNumStr, {
      x: cx + 0.14, y: cardY + bandH * 0.08, w: cardW - 0.20, h: bandH * 0.80,
      fontFace: FD, fontSize: _pcNumFs, bold: true, color: 'FFFFFF',
      align: 'left', valign: 'bottom' });

    // parse heading : body ([icon-name] 접두사 제거)
    const raw = (typeof item === 'object' ? (item.heading || '') : String(item || '')).replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '');
    const colon = raw.indexOf(':');
    const heading = colon > 0 ? raw.slice(0, colon).trim() : raw;
    const desc    = colon > 0 ? raw.slice(colon + 1).trim() : (typeof item === 'object' ? (item.body || '') : '');

    // heading + description — vertically centered in lower card area
    const textAreaY = cardY + bandH + 0.10;
    const textAreaH = cardH - bandH - 0.20;
    const headFs = heading.length > 18 ? 14 : 15;
    const headH = desc ? textAreaH * 0.35 : textAreaH;
    s.addText(heading, {
      x: cx + 0.14, y: textAreaY, w: cardW - 0.28, h: headH,
      fontFace: FH, fontSize: headFs, bold: true, color: C.textPrimary,
      align: 'left', valign: desc ? 'bottom' : 'middle', wrap: true });

    if (desc) {
      s.addText(desc, {
        x: cx + 0.14, y: textAreaY + headH + 0.08, w: cardW - 0.28, h: textAreaH - headH - 0.08,
        fontFace: F, fontSize: 11.5, color: C.textSecondary,
        align: 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.3 });
    }
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW-F: Numbered Process (chevron chain) — 01→02→03→04 순서 흐름
// 용도: 구현 단계, 워크플로우, 프로세스 스텝 (3~5 항목)
// ─────────────────────────────────────────────────────────────────
function pm_addNumberedProcess(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  pm_addSlideFrame(s, C, fonts, title, eyebrow || '');  // absolute layout — divY not used
  const N = Math.min(items.length, 5);
  if (N === 0) return;

  // 레퍼런스 스타일: 큰 숫자(위) + 화살표 라인 + Step명 + 설명(아래)
  const aX = 0.533, aW = 12.267;
  const lineY = 4.20;          // 화살표 라인 y
  const slotW = aW / N;
  const numFs  = N <= 3 ? 58 : N <= 4 ? 50 : 42;  // 큰 숫자 폰트
  const stepFs = N <= 3 ? 15 : 14;
  const descFs = N <= 3 ? 12 : 11;

  // 전체 화살표 라인 (얇은 수평선)
  s.addShape('line', { x: aX, y: lineY, w: aW, h: 0,
    line: { color: C.lineColor, width: 1.0 } });
  // 라인 끝 화살표 캡
  s.addShape('triangle', { x: aX + aW - 0.14, y: lineY - 0.09,
    w: 0.16, h: 0.18,
    fill: { color: C.lineColor }, line: { type: 'none' }, rotate: 90 });

  items.slice(0, N).forEach((item, i) => {
    const cx = aX + slotW * (i + 0.5);
    const tw  = slotW - 0.12;

    // ① 큰 숫자 (라인 위, primary 컬러 — 두 자리 포맷)
    s.addText(String(i + 1).padStart(2, '0'), {
      x: cx - tw / 2, y: lineY - 1.50, w: tw, h: 1.30,
      fontFace: FD, fontSize: numFs, bold: true, color: C.primary,
      align: 'left', valign: 'bottom' });

    // ② 라인 위 수직 연결선 (숫자 → 라인)
    s.addShape('rect', { x: cx - tw / 2 + 0.04, y: lineY - 0.36, w: 0.014, h: 0.36,
      fill: { color: C.lineColor, transparency: 50 }, line: { type: 'none' } });

    // ③ 라인 위 작은 마커 점
    const dotR = 0.055;
    s.addShape('ellipse', { x: cx - tw / 2 + 0.04 - dotR * 0.5, y: lineY - dotR,
      w: dotR * 2, h: dotR * 2,
      fill: { color: C.primary }, line: { type: 'none' } });

    // ④ Step명 (라인 아래, 볼드)
    s.addText(item.heading || '', {
      x: cx - tw / 2, y: lineY + 0.18, w: tw, h: 0.60,
      fontFace: F, fontSize: stepFs, bold: true, color: C.textPrimary,
      align: 'left', valign: 'top', wrap: true });

    // ⑤ 설명 (Step명 아래, muted)
    const descTxt = item.body || '';
    if (descTxt) s.addText(descTxt, {
      x: cx - tw / 2, y: lineY + 0.86, w: tw, h: 2.10,
      fontFace: F, fontSize: descFs, color: C.textSecondary,
      align: 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.45 });

    // ⑥ 단계 사이 화살표 (슬롯 경계)
    if (i < N - 1) {
      const arX = aX + slotW * (i + 1) - 0.22;
      s.addShape('triangle', { x: arX, y: lineY - 0.09,
        w: 0.14, h: 0.18,
        fill: { color: C.primary, transparency: 40 }, line: { type: 'none' }, rotate: 90 });
    }
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW-G: Data Table — 컬러 헤더 행 + 데이터 행 (feature matrix / comparison table)
// 용도: 기능 비교, 가격표, 스펙 비교, 옵션 매트릭스 (2~6행 × 2~5열)
// body 파싱: "행 레이블 | 열1값 | 열2값 | 열3값"
// sub  파싱: "열0헤더 | 열1헤더 | 열2헤더 | 열3헤더" (없으면 자동 생성)
// ─────────────────────────────────────────────────────────────────
function pm_addDataTable(s, C, fonts, title, items, eyebrow, colHeaders) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  if (items.length === 0) return;

  const _parsePipe = str => String(str || '').split('|').map(p => p.trim());

  // 행 파싱
  const rows = items.map(item => {
    if (item.heading && item.body) return [item.heading, ..._parsePipe(item.body)];
    return _parsePipe(item.heading || item);
  });

  const numCols = Math.min(Math.max(...rows.map(r => r.length)), 5);
  const numRows = Math.min(rows.length, 7);

  // 열 헤더: colHeaders 파라미터 → 없으면 자동 번호
  const hdrCells = colHeaders
    ? _parsePipe(colHeaders).slice(0, numCols)
    : ['항목', ...Array.from({ length: numCols - 1 }, (_, i) => `옵션 ${String(i + 1).padStart(2, '0')}`)];

  const tX = 0.533, tY = divY + 1.48, tW = 12.267;
  const hdrH = 0.48;
  const rowH = Math.min((6.90 - tY - hdrH) / numRows, 0.72);  // 6.90" 기준 (copyright 공간 확보)
  const firstColW = tW * 0.22;
  const dataColW = (tW - firstColW) / Math.max(numCols - 1, 1);

  const colX = ci => tX + (ci === 0 ? 0 : firstColW + (ci - 1) * dataColW);
  const colW = ci => ci === 0 ? firstColW : dataColW;

  // ── 헤더 행 ──
  hdrCells.forEach((cell, ci) => {
    const hFill = ci === 0 ? '2D2D2D' : (ci % 2 === 1 ? C.primary : C.accentDark);
    s.addShape('rect', { x: colX(ci), y: tY, w: colW(ci), h: hdrH,
      fill: { color: hFill }, line: { type: 'none' } });
    s.addText(cell, { x: colX(ci) + 0.08, y: tY, w: colW(ci) - 0.16, h: hdrH,
      fontFace: F, fontSize: 10, bold: true, color: 'FFFFFF',
      align: ci === 0 ? 'left' : 'center', valign: 'middle' });
  });

  // ── 데이터 행 ──
  rows.slice(0, numRows).forEach((row, ri) => {
    const ry = tY + hdrH + ri * rowH;
    const isEven = ri % 2 === 0;

    row.slice(0, numCols).forEach((cell, ci) => {
      const bgFill = ci === 0
        ? (isEven ? _pm_bright(C.primary, 0.92) : _pm_bright(C.primary, 0.88))
        : (isEven ? 'FFFFFF' : 'F5F7FA');
      s.addShape('rect', { x: colX(ci), y: ry, w: colW(ci), h: rowH,
        fill: { color: bgFill },
        line: { color: 'E0E0E8', width: 0.5 } });

      // ✓ / ✗ / ● 특수 셀 → primary/red 컬러로 강조
      const isTick = cell === '✓' || cell.toLowerCase() === 'o' || cell === '●';
      const isCross = cell === '✗' || cell.toLowerCase() === 'x' || cell === '×';
      const dispText = isTick ? '✓' : isCross ? '✗' : cell;
      const dispColor = isTick ? C.primary : isCross ? 'CC3333' : (ci === 0 ? C.textPrimary : C.textSecondary);

      s.addText(dispText, { x: colX(ci) + 0.08, y: ry, w: colW(ci) - 0.16, h: rowH,
        fontFace: F, fontSize: ci === 0 ? 10 : 9.5,
        bold: ci === 0 || isTick || isCross,
        color: dispColor,
        align: ci === 0 ? 'left' : 'center', valign: 'middle',
        wrap: ci === 0 });
    });
  });

  // 테이블 하단 경계선
  const tableBottom = tY + hdrH + Math.min(numRows, rows.length) * rowH;
  s.addShape('line', { x: tX, y: tableBottom, w: tW, h: 0,
    line: { color: C.primary, width: 1.5 } });
}

// ─────────────────────────────────────────────────────────────────
// NEW-A: Horizontal Arrow Timeline (10p) — left-to-right schedule flow
// 용도: 일정·타임라인이 왼쪽→오른쪽으로 흘러가는 내용
// ─────────────────────────────────────────────────────────────────
function pm_addHorizontalArrowTimeline(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 6);
  if (N === 0) return;
  // Reference design: 점(dot) + Phase 라벨 위 + Step명·설명 아래
  const trackX = 0.80, trackW = 12.00;
  const trackY = 3.60;   // 선 y 위치
  const slot = trackW / N;
  const dotR = 0.085;    // 작은 점 반지름

  // 수평 메인 선 (얇고 선명)
  s.addShape('rect', { x: trackX, y: trackY - 0.012, w: trackW, h: 0.024,
    fill: { color: C.lineColor }, line: { type: 'none' } });
  // 우측 화살표 캡
  s.addShape('triangle', { x: trackX + trackW - 0.13, y: trackY - 0.09,
    w: 0.15, h: 0.18,
    fill: { color: C.lineColor }, line: { type: 'none' }, rotate: 90 });

  for (let i = 0; i < N; i++) {
    const cx = trackX + slot * (i + 0.5);
    const tw = slot - 0.10;

    // ① Phase 라벨 — 선 위 (PHASE N 또는 items[i].label)
    const rawLabel = items[i].label || String(i + 1);
    // 숫자만이면 "PHASE N" 형태로, 아니면 원본 그대로
    const phaseStr = /^\d+$/.test(rawLabel) ? `PHASE ${rawLabel}` : rawLabel.toUpperCase();
    s.addText(phaseStr, {
      x: cx - tw / 2, y: trackY - 0.92, w: tw, h: 0.28,
      fontFace: F, fontSize: 8, bold: true, color: C.primary, charSpacing: 0.5,
      align: 'center', valign: 'middle' });

    // ② 선 위 수직 연결선 (Phase 라벨 ↔ 점)
    s.addShape('rect', { x: cx - 0.008, y: trackY - 0.62, w: 0.016, h: 0.62,
      fill: { color: C.lineColor, transparency: 55 }, line: { type: 'none' } });

    // ③ 점 (primary 색상, 짝수는 accentDark)
    const dotFill = i % 2 === 0 ? C.primary : C.accentDark;
    s.addShape('ellipse', { x: cx - dotR, y: trackY - dotR, w: dotR * 2, h: dotR * 2,
      fill: { color: dotFill }, line: { type: 'none' } });

    // ④ Step명 (점 아래, 볼드)
    const stepFontSize = N <= 3 ? 14 : N <= 4 ? 12 : 11;
    s.addText(items[i].heading || '', {
      x: cx - tw / 2, y: trackY + dotR + 0.14, w: tw, h: 0.55,
      fontFace: FH, fontSize: stepFontSize, bold: true, color: C.textPrimary,
      align: 'center', valign: 'top', wrap: true });

    // ⑤ 설명 텍스트 (Step명 아래)
    s.addText(items[i].body || '', {
      x: cx - tw / 2, y: trackY + dotR + 0.80, w: tw, h: 2.60,
      fontFace: F, fontSize: N <= 3 ? 11.5 : 10.5, color: C.textSecondary,
      align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.35 });
  }
}

// ─────────────────────────────────────────────────────────────────
// NEW-B: Circle Diagram 4 (8p) — 4개 동등한 항목 묶음
// 용도: 4가지 병렬/동등한 주제를 함께 묶어 보여줄 때
// ─────────────────────────────────────────────────────────────────
function pm_addCircleDiagram4(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const areaX = 0.533, areaY = divY + 1.48;
  const cellW = 6.135, cellH = 2.36;
  const circD = 1.50;
  const fills = [C.primary, C.accentDark, C.accentDark, C.primary];

  // 격자 구분선 (먼저 그림)
  s.addShape('line', { x: areaX + cellW, y: areaY + 0.08, w: 0, h: cellH * 2 - 0.16,
    line: { color: C.lineColor, width: 0.5 } });
  s.addShape('line', { x: areaX + 0.08, y: areaY + cellH, w: cellW * 2 - 0.16, h: 0,
    line: { color: C.lineColor, width: 0.5 } });

  items.slice(0, 4).forEach((item, idx) => {
    const col = idx % 2, row = idx >> 1;
    const cellX = areaX + col * cellW;
    const cellY = areaY + row * cellH;
    const cx = cellX + 0.28;
    const cy = cellY + (cellH - circD) / 2;

    // 원
    s.addShape('ellipse', { x: cx, y: cy, w: circD, h: circD,
      fill: { color: fills[idx] }, line: { type: 'none' } });
    s.addText(String(idx + 1), { x: cx, y: cy, w: circD, h: circD,
      fontFace: F, fontSize: 22, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle' });

    // 텍스트 (원 오른쪽)
    const tx = cx + circD + 0.22, tw = cellW - circD - 0.72;
    s.addText([
      { text: item.heading || '', options: { fontFace: FH, fontSize: 14, bold: true,
          color: C.textPrimary, breakLine: true }},
      { text: item.body    || '', options: { fontFace: F, fontSize: 11, color: C.textSecondary }},
    ], { x: tx, y: cy, w: tw, h: circD,
         valign: 'middle', wrap: true, lineSpacingMultiple: 1.3 });
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW-C: Converge Diagram 4 (13p) — 4개가 중앙으로 수렴
// 용도: 4가지가 합쳐져서 가운데 핵심 개념을 만들 때
// ─────────────────────────────────────────────────────────────────
function pm_addConvergeDiagram4(s, C, fonts, title, items, centerLabel, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const ccx = 6.667, ccy = 4.92, cd = 1.80;

  // 중앙 원
  s.addShape('ellipse', { x: ccx - cd/2, y: ccy - cd/2, w: cd, h: cd,
    fill: { color: C.primary }, line: { type: 'none' } });
  s.addText(centerLabel || '', { x: ccx - cd/2, y: ccy - cd/2, w: cd, h: cd,
    fontFace: FH, fontSize: 11, bold: true, color: C.textOnPrimary,
    align: 'center', valign: 'middle', wrap: true });

  // 4개 입력 위치 (십자: 상/우/하/좌)
  const id = 1.05;
  const inputPos = [
    { cx: ccx,         cy: 2.98 },   // 상
    { cx: ccx + 3.75,  cy: ccy  },   // 우
    { cx: ccx,         cy: 6.86 },   // 하
    { cx: ccx - 3.75,  cy: ccy  },   // 좌
  ];

  inputPos.slice(0, Math.min(items.length, 4)).forEach((pos, idx) => {
    // 입력 원
    s.addShape('ellipse', { x: pos.cx - id/2, y: pos.cy - id/2, w: id, h: id,
      fill: { color: C.accentDark }, line: { type: 'none' } });
    s.addText(String(idx + 1), { x: pos.cx - id/2, y: pos.cy - id/2, w: id, h: id,
      fontFace: F, fontSize: 13, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle' });

    // 연결선 (입력원 → 중앙원)
    const dx = ccx - pos.cx, dy = ccy - pos.cy;
    const dist = Math.sqrt(dx*dx + dy*dy) || 0.01;
    const fx = pos.cx + (dx/dist)*(id/2+0.06),  fy = pos.cy + (dy/dist)*(id/2+0.06);
    const tx = ccx  - (dx/dist)*(cd/2+0.06),    ty = ccy  - (dy/dist)*(cd/2+0.06);
    const lx = Math.min(fx, tx), ly = Math.min(fy, ty);
    const lw = Math.max(Math.abs(tx-fx), 0.01),  lh = Math.max(Math.abs(ty-fy), 0.01);
    s.addShape('line', { x: lx, y: ly, w: lw, h: lh,
      flipH: fx > tx, flipV: fy > ty,
      line: { color: C.accentLight, width: 1.5 } });

    // 텍스트 레이블
    const item = items[idx];
    const tw2 = 2.35, th2 = 0.90;
    let lbX, lbY, align;
    if (idx === 0) { lbX = pos.cx - tw2/2; lbY = pos.cy - id/2 - th2 - 0.06; align = 'center'; }
    else if (idx === 1) { lbX = pos.cx + id/2 + 0.10; lbY = pos.cy - th2/2; align = 'left'; }
    else if (idx === 2) { lbX = pos.cx - tw2/2; lbY = pos.cy + id/2 + 0.06; align = 'center'; }
    else { lbX = pos.cx - id/2 - tw2 - 0.10; lbY = pos.cy - th2/2; align = 'right'; }

    s.addText([
      { text: item.heading || '', options: { fontFace: FH, fontSize: 12, bold: true,
          color: C.textPrimary, breakLine: true }},
      { text: item.body    || '', options: { fontFace: F, fontSize: 10, color: C.textSecondary }},
    ], { x: lbX, y: lbY, w: tw2, h: th2,
         valign: 'top', wrap: true, align, lineSpacingMultiple: 1.25 });
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW-D: Linked Diagram 4 (15p) — 4개가 서로 연결/영향
// 용도: 4가지가 서로 영향을 주고받는 내용 (SWOT 등 포함)
// ─────────────────────────────────────────────────────────────────
function pm_addLinkedDiagram4(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const circD = 1.42;
  // 4개 원 (2×2 배치 — 좌상/우상/좌하/우하)
  const pos = [
    { cx: 3.20,  cy: 3.42 },
    { cx: 10.13, cy: 3.42 },
    { cx: 3.20,  cy: 6.22 },
    { cx: 10.13, cy: 6.22 },
  ];
  const fills = [C.primary, C.accentDark, C.accentDark, C.primary];

  // 연결선 먼저 (원 뒤쪽)
  [[0,1],[1,3],[3,2],[2,0]].forEach(([a,b]) => {
    const pa = pos[a], pb = pos[b];
    const lx = Math.min(pa.cx, pb.cx), ly = Math.min(pa.cy, pb.cy);
    const lw = Math.max(Math.abs(pb.cx-pa.cx), 0.01);
    const lh = Math.max(Math.abs(pb.cy-pa.cy), 0.01);
    s.addShape('line', { x: lx, y: ly, w: lw, h: lh,
      flipH: pa.cx > pb.cx, flipV: pa.cy > pb.cy,
      line: { color: C.accentLight, width: 1.2, dashType: 'dash' } });
  });

  pos.slice(0, Math.min(items.length, 4)).forEach((p, idx) => {
    const col = idx % 2; // 0=left, 1=right
    s.addShape('ellipse', { x: p.cx - circD/2, y: p.cy - circD/2, w: circD, h: circD,
      fill: { color: fills[idx] }, line: { type: 'none' } });
    s.addText(String(idx + 1), { x: p.cx - circD/2, y: p.cy - circD/2, w: circD, h: circD,
      fontFace: F, fontSize: 18, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle' });

    // 텍스트: 왼쪽 원 → 왼쪽에 텍스트, 오른쪽 원 → 오른쪽에 텍스트
    const tw = 2.90, th = 1.10;
    const tx = col === 0 ? p.cx - circD/2 - tw - 0.12 : p.cx + circD/2 + 0.12;
    const ty = p.cy - th/2;
    const align = col === 0 ? 'right' : 'left';
    s.addText([
      { text: items[idx].heading || '', options: { fontFace: FH, fontSize: 13, bold: true,
          color: C.textPrimary, breakLine: true }},
      { text: items[idx].body    || '', options: { fontFace: F, fontSize: 10.5, color: C.textSecondary }},
    ], { x: tx, y: ty, w: tw, h: th,
         valign: 'middle', wrap: true, align, lineSpacingMultiple: 1.3 });
  });
}

// ─────────────────────────────────────────────────────────────────
// NEW-F: SWOT 4-Grid — 레퍼런스 기반 2×2 그리드
// 용도: swot_analysis 슬라이드 — 강점/약점/기회/위협 4개 카드
// ─────────────────────────────────────────────────────────────────
function pm_addSwot4Grid(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const aX=0.28, aY=divY + 0.16, aW=12.773, aH=6.00;
  const gap=0.14, qW=(aW-gap)/2, qH=(aH-gap)/2;
  const labels = ['Strength (강점)','Weakness (약점)','Opportunity (기회)','Threat (위협)'];
  const qPos = [
    { x: aX,         y: aY },
    { x: aX+qW+gap,  y: aY },
    { x: aX,         y: aY+qH+gap },
    { x: aX+qW+gap,  y: aY+qH+gap }
  ];
  const hdrH = 0.48;

  items.slice(0, 4).forEach((item, i) => {
    const { x, y } = qPos[i];
    // 카드 배경
    s.addShape('roundRect', { x, y, w: qW, h: qH,
      fill: { color: _pm_bright(C.primary, 0.91) },
      line: { color: C.lineColor, width: 0.5 }, rectRadius: 0.14, shadow: PM_CARD_SHADOW });
    // 헤더 (primary 텍스트)
    s.addText(labels[i], { x: x+0.18, y: y+0.10, w: qW-0.36, h: hdrH,
      fontFace: FH, fontSize: 14, bold: true, color: C.primary,
      align: 'center', valign: 'middle' });
    // 구분선
    s.addShape('line', { x: x+0.18, y: y+hdrH+0.12, w: qW-0.36, h: 0,
      line: { color: C.lineColor, width: 0.5 } });
    // 아이템 목록
    const bodyArr = Array.isArray(item.body)
      ? item.body
      : String(item.body || item.heading || '').split(/[,，·\n]/).map(t=>t.trim()).filter(Boolean);
    let iy = y + hdrH + 0.26;
    bodyArr.slice(0, 3).forEach(b => {
      if (iy + 0.52 > y + qH - 0.10) return;
      s.addText('✓  ' + b, { x: x+0.20, y: iy, w: qW-0.40, h: 0.52,
        fontFace: F, fontSize: 11, color: C.textSecondary,
        valign: 'top', wrap: true, lineSpacingMultiple: 1.3 });
      iy += 0.56;
    });
  });

  // Center SWOT 배지
  const bdW=1.40, bdH=0.46;
  const bdX=aX+aW/2-bdW/2, bdY=aY+aH/2-bdH/2;
  s.addShape('roundRect', { x: bdX, y: bdY, w: bdW, h: bdH,
    fill: { color: C.primary }, line: { type: 'none' }, rectRadius: 0.14 });
  s.addText('SWOT', { x: bdX, y: bdY, w: bdW, h: bdH,
    fontFace: F, fontSize: 14, bold: true, color: C.textOnPrimary,
    align: 'center', valign: 'middle' });
}

// ─────────────────────────────────────────────────────────────────
// NEW-E: Gear Process (18p) — N개 기어가 유기적으로 맞물리는 프로세스
// 용도: N가지 단계/구성요소가 함께 돌아갈 때 (N=3~6)
// ─────────────────────────────────────────────────────────────────
function pm_addGearProcess(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 6);
  if (N === 0) return;
  const areaX = 0.533, areaY = divY + 1.61, areaW = 12.267;
  const slot = areaW / N;
  const baseY = areaY + 1.55; // 기어 체인 중심 Y

  for (let i = 0; i < N; i++) {
    const isLarge = i % 2 === 0;
    const d = isLarge ? Math.min(slot * 0.78, 2.10) : Math.min(slot * 0.62, 1.65);
    const cx = areaX + slot * (i + 0.5);
    const cy = isLarge ? baseY : baseY + 0.22;

    // 기어 이빨 효과: 점선 외부 링
    const od = d + 0.28;
    s.addShape('ellipse', { x: cx - od/2, y: cy - od/2, w: od, h: od,
      fill: { type: 'none' },
      line: { color: isLarge ? C.primary : C.accentDark, width: 7, dashType: 'sysDash' } });

    // 기어 본체
    s.addShape('ellipse', { x: cx - d/2, y: cy - d/2, w: d, h: d,
      fill: { color: isLarge ? C.primary : C.accentDark }, line: { type: 'none' } });

    // 기어 중심 구멍
    const hd = d * 0.28;
    s.addShape('ellipse', { x: cx - hd/2, y: cy - hd/2, w: hd, h: hd,
      fill: { color: C.bg }, line: { type: 'none' } });

    // 기어 내부 라벨
    const fs = Math.max(Math.min(Math.round(d * 5.8), 11), 8);
    s.addText(items[i].heading || String(i+1), {
      x: cx - d/2 + 0.08, y: cy - d/2 + 0.06, w: d - 0.16, h: d * 0.50,
      fontFace: FH, fontSize: fs, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle', wrap: true });

    // 하단 설명 텍스트
    if (items[i].body) {
      const tw = Math.max(slot - 0.14, 1.0);
      s.addText(items[i].body, {
        x: cx - tw/2, y: cy + d/2 + od/2 - d/2 + 0.16, w: tw, h: 1.55,
        fontFace: F, fontSize: 10.5, color: C.textSecondary,
        align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.3 });
    }
  }
}

// ─────────────────────────────────────────────────────────────────
// NEW: Stat 3 Col — 3열 대형 퍼센트/숫자 레이아웃
// 용도: 핵심 지표 3개를 대형 숫자로 강조할 때 (45% / 22% / 52%)
// ─────────────────────────────────────────────────────────────────
function pm_addStat3Col(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 4);  // 최대 4개 (4개: 2×2 그리드)
  if (N === 0) return;
  const aXFull = 0.533, aY = divY + 0.71, aWFull = 12.267, aH = 4.80;
  // 1개짜리: 60% 폭 중앙 집중형 (전체 폭 사용 시 너무 공허)
  const aW = N === 1 ? aWFull * 0.60 : aWFull;
  const aX = N === 1 ? aXFull + (aWFull - aW) / 2 : aXFull;

  // 컬러 팔레트: accent 베리에이션 (30%/50%/62% 어둡게 — 카드별 차이 뚜렷)
  const statPalette = [_pm_bright(C.primary, -0.30), _pm_bright(C.primary, -0.50), _pm_bright(C.primary, -0.62)];
  const colGap = 0.18;
  // N=4: 2열 2행 그리드 / N<=3: 1행 N열
  const cols = N <= 3 ? N : 2;
  const rows = N <= 3 ? 1 : 2;
  const rowGap = N === 4 ? 0.16 : 0;
  const colW2 = (aW - colGap * (cols - 1)) / cols;  // 간격 포함 실제 컬럼 너비
  const rowH2 = rows === 2 ? (aH - rowGap) / 2 : aH;  // 행 높이

  // ── N===1 특수 처리: 좌(숫자)/우(레이블+설명) 분리 레이아웃 ──────────
  if (N === 1) {
    const item = items[0];
    const valStr   = String(item.value || '');
    const unitStr  = String(item.unit || '');
    const labelStr = String(item.label || '');
    const descStr  = String(item.desc || item.body || '');

    // 카드 배경
    s.addShape('roundRect', { x: aX, y: aY, w: aW, h: aH,
      fill: { color: C.primary }, line: { type: 'none' }, rectRadius: 0.15 });

    if (valStr) {
      // 좌측: 숫자 + 단위 (45%)
      const lW = aW * 0.44;
      const valFontSize = valStr.length <= 3 ? 90 : valStr.length <= 5 ? 66 : 48;
      s.addText(valStr, { x: aX + aW * 0.02, y: aY + aH * 0.08, w: lW, h: aH * 0.52,
        fontFace: FD, fontSize: valFontSize, bold: true, color: 'FFFFFF',
        align: 'center', valign: 'middle' });
      if (unitStr) s.addText(unitStr, { x: aX + lW * 0.65, y: aY + aH * 0.52, w: lW * 0.5, h: aH * 0.16,
        fontFace: FD, fontSize: 28, bold: true, color: 'FFFFFF', align: 'left', valign: 'top' });
      // 수직 구분선
      s.addShape('rect', { x: aX + aW * 0.47, y: aY + aH * 0.12, w: 0.03, h: aH * 0.76,
        fill: { color: 'FFFFFF', transparency: 60 }, line: { type: 'none' } });
      // 우측: 레이블 + 설명 (53%)
      const rX = aX + aW * 0.50, rW = aW * 0.46;
      s.addText(labelStr, { x: rX, y: aY + aH * 0.18, w: rW, h: aH * 0.30,
        fontFace: FH, fontSize: 24, bold: true, color: 'FFFFFF',
        align: 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.3 });
      if (descStr) s.addText(descStr, { x: rX, y: aY + aH * 0.52, w: rW, h: aH * 0.38,
        fontFace: F, fontSize: 15, color: 'FFFFFF', transparency: 10,
        align: 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.4 });
    } else {
      // 텍스트 전용 단일 카드: 중앙 배치
      s.addText(labelStr, { x: aX + aW * 0.05, y: aY + aH * 0.22, w: aW * 0.90, h: aH * 0.34,
        fontFace: FH, fontSize: 26, bold: true, color: 'FFFFFF',
        align: 'center', valign: 'middle', wrap: true, lineSpacingMultiple: 1.4 });
      if (descStr) s.addText(descStr, { x: aX + aW * 0.08, y: aY + aH * 0.60, w: aW * 0.84, h: aH * 0.28,
        fontFace: F, fontSize: 15, color: 'FFFFFF',
        align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.4 });
    }
    return;
  }

  for (let i = 0; i < N; i++) {
    const item = items[i];
    const col = N <= 3 ? i : i % 2;
    const row = N <= 3 ? 0 : Math.floor(i / 2);
    const x  = aX + col * (colW2 + colGap);
    const cy = aY + row * (rowH2 + rowGap);  // 현재 카드 Y 시작
    const cH = rowH2;                          // 현재 카드 높이
    const valStr = String(item.value || '');   // 빈 문자열 그대로 — '—' fallback 제거
    const unitStr = String(item.unit || '');
    const labelStr = String(item.label || '');
    const descStr = String(item.desc || item.body || '');
    const panelColor = statPalette[i % statPalette.length];

    // 컬러 패널 배경 (레퍼런스처럼 컬럼 전체를 색으로 채움)
    s.addShape('roundRect', {
      x: x, y: cy, w: colW2, h: cH,
      fill: { color: panelColor }, line: { type: 'none' }, rectRadius: 0.15 });

    if (valStr && valStr !== '') {
      // ── 숫자 통계 모드 — 숫자+단위 통합 중앙 정렬 ──
      const fullVal = valStr + (unitStr ? '\u00A0' + unitStr : '');  // non-breaking space
      const fullLen = valStr.length + (unitStr ? unitStr.length + 1 : 0);
      const valFontSize = N === 4
        ? (fullLen <= 4 ? 52 : fullLen <= 6 ? 40 : 30)
        : (fullLen <= 4 ? 76 : fullLen <= 7 ? 56 : 42);
      s.addText(fullVal, {
        x: x + colW2 * 0.05, y: cy + cH * 0.05, w: colW2 * 0.90, h: cH * 0.48,
        wrap: false, shrinkText: true,
        fontFace: FD, fontSize: valFontSize, bold: true, color: 'FFFFFF',
        align: 'center', valign: 'middle' });

      // 구분선
      s.addShape('rect', { x: x + colW2 * 0.08, y: cy + cH * 0.55, w: colW2 * 0.84, h: 0.025,
        fill: { color: 'FFFFFF', transparency: 55 }, line: { type: 'none' } });

      // 라벨
      s.addText(labelStr, {
        x: x + colW2 * 0.05, y: cy + cH * 0.58, w: colW2 * 0.90, h: cH * 0.24,
        fontFace: F, fontSize: N === 4 ? 12 : 14, bold: true, color: 'FFFFFF',
        align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.3 });

      if (descStr) {
        s.addText(descStr, {
          x: x + colW2 * 0.05, y: cy + cH * 0.82, w: colW2 * 0.90, h: cH * 0.15,
          fontFace: F, fontSize: N === 4 ? 10 : 11.5, color: 'FFFFFF',
          align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.2 });
      }
    } else {
      // ── 텍스트 카드 모드 ("제목: 설명" 형식) ──
      // 상단 아이콘/번호 원 (카드 상단 중앙)
      const bdD = Math.min(colW2 * 0.22, 0.72);
      const bdX = x + colW2 / 2 - bdD / 2;
      s.addShape('ellipse', { x: bdX, y: cy + cH * 0.06, w: bdD, h: bdD,
        fill: { color: 'FFFFFF', transparency: 30 }, line: { type: 'none' } });
      s.addText(`${i + 1}`, { x: bdX, y: cy + cH * 0.06, w: bdD, h: bdD,
        fontFace: F, fontSize: Math.round(bdD * 24), bold: true, color: 'FFFFFF',
        align: 'center', valign: 'middle' });

      // 구분선
      s.addShape('rect', { x: x + colW2 * 0.08, y: cy + cH * 0.32, w: colW2 * 0.84, h: 0.025,
        fill: { color: 'FFFFFF', transparency: 55 }, line: { type: 'none' } });

      // 제목 (bold, 큰 텍스트)
      s.addText(labelStr, {
        x: x + colW2 * 0.05, y: cy + cH * 0.36, w: colW2 * 0.90, h: cH * 0.22,
        fontFace: F, fontSize: N === 4 ? 14 : 16, bold: true, color: 'FFFFFF',
        align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.25 });

      // 설명 (작은 텍스트, 하단)
      if (descStr) {
        s.addText(descStr, {
          x: x + colW2 * 0.05, y: cy + cH * 0.60, w: colW2 * 0.90, h: cH * 0.36,
          fontFace: F, fontSize: N === 4 ? 10 : 11, color: 'FFFFFF',
          align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.3 });
      }
    }
  }
}

// ─────────────────────────────────────────────────────────────────
// NEW: Stat Grid — 숫자 박스 그리드 (최대 3×3)
// 용도: 6~9개 수치를 격자로 표시하는 데이터 집약 슬라이드
// ─────────────────────────────────────────────────────────────────
function pm_addStatGrid(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 9);
  if (N === 0) return;
  const cols = N <= 4 ? 2 : 3;
  const rows = Math.ceil(N / cols);
  const gridX = 0.533, gridY = divY + 0.58, gridW = 12.267, gridH = 5.42;
  const gap = 0.14;
  const boxW = (gridW - gap * (cols - 1)) / cols;
  const boxH = (gridH - gap * (rows - 1)) / rows;

  const FILLS = [C.primary, C.accentDark, _pm_bright(C.primary, 0.38)];

  for (let i = 0; i < N; i++) {
    const item = items[i];
    const col = i % cols;
    const row = Math.floor(i / cols);
    const bx = gridX + col * (boxW + gap);
    const by = gridY + row * (boxH + gap);
    const fill = FILLS[i % FILLS.length];
    const isLight = _pm_light('#' + fill);
    const txtClr  = isLight ? C.textPrimary : C.textOnPrimary;
    const subClr  = isLight ? C.textSecondary : _pm_bright(fill, 0.55);

    s.addShape('roundRect', { x: bx, y: by, w: boxW, h: boxH,
      fill: { color: fill }, line: { type: 'none' }, rectRadius: 0.16, shadow: PM_CARD_SHADOW });

    // 대형 숫자 + 단위
    const valStr = String(item.value || '—') + String(item.unit || '');
    s.addText(valStr, {
      x: bx + boxW * 0.06, y: by + boxH * 0.08, w: boxW * 0.88, h: boxH * 0.52,
      fontFace: FD, fontSize: rows <= 2 ? 36 : 26, bold: true, color: txtClr,
      align: 'center', valign: 'middle' });

    // 라벨
    s.addText(item.label || '', {
      x: bx + boxW * 0.06, y: by + boxH * 0.62, w: boxW * 0.88, h: boxH * 0.35,
      fontFace: F, fontSize: rows <= 2 ? 11.5 : 10, color: subClr,
      align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.25 });
  }
}

// ─────────────────────────────────────────────────────────────────
// NEW: Vertical Timeline — 수직 교차 타임라인
// 용도: 연도별 이력, 로드맵, 성장 스토리 (최대 6단계)
// ─────────────────────────────────────────────────────────────────
function pm_addVerticalTimeline(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 6);
  if (N === 0) return;
  const aX = 0.533, aY = divY + 0.58, aW = 12.267, aH = 5.42;
  const lineX = aX + aW / 2;  // 중앙 수직선 X
  const stepH = aH / N;
  const markerD = 0.32;
  const textW = aW * 0.42;

  // 중앙 수직선
  s.addShape('rect', { x: lineX - 0.015, y: aY, w: 0.03, h: aH,
    fill: { color: C.primary, transparency: 30 }, line: { type: 'none' } });

  for (let i = 0; i < N; i++) {
    const item = items[i];
    const cy = aY + stepH * (i + 0.5);  // 항목 중심 Y
    const isLeft = i % 2 === 0;          // 짝수: 텍스트 좌측, 홀수: 우측
    const markerX = lineX - markerD / 2;
    const markerY = cy - markerD / 2;

    // 마커 원
    s.addShape('ellipse', { x: markerX, y: markerY, w: markerD, h: markerD,
      fill: { color: i % 2 === 0 ? C.primary : C.accentDark }, line: { type: 'none' } });

    // 마커 내부 번호/날짜
    const markerLabel = item.date || String(i + 1);
    s.addText(markerLabel, { x: markerX, y: markerY, w: markerD, h: markerD,
      fontFace: F, fontSize: 7, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle' });

    // 수평 연결선 (마커 → 텍스트박스)
    const connLen = aW * 0.06;
    if (isLeft) {
      s.addShape('rect', { x: lineX - markerD / 2 - connLen, y: cy - 0.012, w: connLen, h: 0.024,
        fill: { color: C.lineColor }, line: { type: 'none' } });
    } else {
      s.addShape('rect', { x: lineX + markerD / 2, y: cy - 0.012, w: connLen, h: 0.024,
        fill: { color: C.lineColor }, line: { type: 'none' } });
    }

    // 텍스트 박스
    const txtX = isLeft ? aX : lineX + markerD / 2 + connLen + 0.04;
    const txtMaxW = isLeft ? (lineX - markerD / 2 - connLen - aX - 0.06) : (aX + aW - txtX - 0.04);
    const txtY = cy - stepH * 0.44;
    const txtH = stepH * 0.88;

    // 배경 카드 (아주 연하게)
    s.addShape('roundRect', { x: txtX - 0.06, y: txtY, w: txtMaxW + 0.12, h: txtH,
      fill: { color: C.accentLight, transparency: 80 }, line: { type: 'none' }, rectRadius: 0.12 });

    // 제목
    s.addText(item.heading || item.label || '', {
      x: txtX, y: txtY + txtH * 0.06, w: txtMaxW, h: txtH * 0.42,
      fontFace: FH, fontSize: 11, bold: true, color: C.textPrimary,
      align: isLeft ? 'right' : 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.2 });

    // 설명
    if (item.body || item.desc) {
      s.addText(item.body || item.desc, {
        x: txtX, y: txtY + txtH * 0.50, w: txtMaxW, h: txtH * 0.46,
        fontFace: F, fontSize: 10.5, color: C.textSecondary,
        align: isLeft ? 'right' : 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.3 });
    }
  }
}

// ─────────────────────────────────────────────────────────────────
// NEW: Comparison VS — A vs B 2열 비교 레이아웃
// 용도: 2개 옵션/솔루션/이전-이후 대비
// ─────────────────────────────────────────────────────────────────
function pm_addComparisonVS(s, C, fonts, title, leftItems, rightItems, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const aX = 0.533, aY = divY + 0.66, aW = 12.267, aH = 5.36;
  const vsD = 0.62;
  const gap = 0.20;
  const cardW = (aW - vsD - gap * 4) / 2;
  const leftX = aX + gap;
  const rightX = aX + aW - gap - cardW;

  const renderCard = (x, items, isPrimary) => {
    const N = Math.min(items.length, 5);
    const headerH = 0.52;
    const bodyH = aH - headerH - 0.14;
    const fill = isPrimary ? C.primary : _pm_bright(C.primary, -0.22);
    const isLight = _pm_light('#' + fill);

    // 헤더
    s.addShape('roundRect', { x, y: aY, w: cardW, h: headerH,
      fill: { color: fill }, line: { type: 'none' }, rectRadius: 0.14 });
    s.addText(items[0] ? (items[0].groupLabel || (isPrimary ? 'Option A' : 'Option B')) : '',
      { x: x + 0.14, y: aY, w: cardW - 0.28, h: headerH,
        fontFace: FH, fontSize: 14, bold: true,
        color: isLight ? C.textPrimary : C.textOnPrimary,
        align: 'center', valign: 'middle' });

    // 바디 카드
    s.addShape('roundRect', { x, y: aY + headerH + 0.08, w: cardW, h: bodyH,
      fill: { color: C.bg }, line: { color: C.lineColor, width: 1 }, rectRadius: 0.14, shadow: PM_CARD_SHADOW });

    // 수평 진행바 목록
    const barAreaY = aY + headerH + 0.22;
    const barH = 0.20;
    const barGap = bodyH / Math.max(N, 1);
    const maxBarItems = Math.min(N, 5);
    for (let i = 0; i < maxBarItems; i++) {
      const item = items[i] || {};
      const by = barAreaY + barGap * i;
      const barW = cardW - 0.32;
      const barX = x + 0.16;

      // 라벨
      s.addText(item.label || item.heading || '', {
        x: barX, y: by, w: barW * 0.60, h: 0.20,
        fontFace: F, fontSize: 10.5, color: C.textPrimary,
        align: 'left', valign: 'middle' });

      // 퍼센트 값 (오른쪽)
      const pctVal = item.value ? String(item.value) + (item.unit || '') : '';
      if (pctVal) {
        s.addText(pctVal, {
          x: barX + barW * 0.62, y: by, w: barW * 0.38, h: 0.20,
          fontFace: F, fontSize: 10.5, bold: true, color: isPrimary ? C.primary : C.accentDark,
          align: 'right', valign: 'middle' });
      }

      // 진행바 배경
      s.addShape('roundRect', { x: barX, y: by + 0.22, w: barW, h: barH,
        fill: { color: C.accentLight, transparency: 55 }, line: { type: 'none' }, rectRadius: barH / 2 });

      // 진행바 전경
      const pct = Math.min(parseFloat(item.value) || 60, 100) / 100;
      if (pct > 0) {
        s.addShape('roundRect', { x: barX, y: by + 0.22, w: barW * pct, h: barH,
          fill: { color: isPrimary ? C.primary : C.accentDark }, line: { type: 'none' }, rectRadius: barH / 2 });
      }
    }
  };

  renderCard(leftX, leftItems, false);
  renderCard(rightX, rightItems, true);

  // 중앙 VS 배지
  const vsX = aX + aW / 2 - vsD / 2;
  const vsY = aY + aH / 2 - vsD / 2;
  s.addShape('ellipse', { x: vsX, y: vsY, w: vsD, h: vsD,
    fill: { color: C.primary }, line: { color: C.bg, width: 3 } });
  s.addText('VS', { x: vsX, y: vsY, w: vsD, h: vsD,
    fontFace: F, fontSize: 14, bold: true, color: C.textOnPrimary,
    align: 'center', valign: 'middle' });
}

// ── 문제-해결 대조 슬라이드 (좌: AS-IS 어두운 패널 / 우: TO-BE primary 패널) ──
function pm_addProblemSolution(s, C, fonts, title, slide, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  // ① 공통 프레임 (배경·아이웨어·헤드라인)
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');

  const before = slide.before || { label: 'AS-IS', points: [] };
  const after  = slide.after  || { label: 'TO-BE',  points: [] };
  const bLabel = (before.label || 'AS-IS').toUpperCase();
  const aLabel = (after.label  || 'TO-BE').toUpperCase();
  const bPts   = (before.points || []).slice(0, 4);
  const aPts   = (after.points  || []).slice(0, 4);
  const N      = Math.max(bPts.length, aPts.length, 1);

  // ── 레이아웃 치수 ──
  const cX = 0.533, cY = divY + 0.28;
  const cW = W - cX - 0.28;
  const cH = H - cY - 0.32;

  const arrowZoneW = 0.72;           // 중앙 화살표 영역
  const leftW  = cW * 0.44;          // 왼쪽 패널 (문제, 약간 좁게)
  const rightW = cW - leftW - arrowZoneW;  // 오른쪽 패널 (해결, 더 넓게)
  const leftX  = cX;
  const rightX = cX + leftW + arrowZoneW;
  const arrowCX = cX + leftW + arrowZoneW / 2;

  // ── 왼쪽 패널 (AS-IS: 밝은 회색 배경 — Brandlogy Before 스타일, G-1) ──
  s.addShape('roundRect', { x: leftX, y: cY, w: leftW, h: cH,
    fill: { color: 'E8E8EC' }, line: { type: 'none' }, rectRadius: 0.18,
    shadow: PM_CARD_SHADOW });

  // 왼쪽 라벨 칩 (어두운 회색 pill)
  const chipH = 0.32;
  const chipPad = 0.20;
  s.addShape('roundRect', { x: leftX + chipPad, y: cY + 0.24, w: leftW - chipPad * 2, h: chipH,
    fill: { color: '555555' }, line: { type: 'none' }, rectRadius: chipH / 2 });
  s.addText(bLabel, { x: leftX + chipPad, y: cY + 0.24, w: leftW - chipPad * 2, h: chipH,
    fontFace: FH, fontSize: 11, bold: true, color: 'FFFFFF',
    align: 'center', valign: 'middle', charSpacing: 2 });

  // 왼쪽 불릿 (✗ + 텍스트)
  const bBulletY0 = cY + 0.70;
  const bRowH = (cH - 0.70 - 0.20) / Math.max(N, 1);
  bPts.forEach((pt, i) => {
    const by = bBulletY0 + bRowH * i;
    const [head, ...rest] = pt.split(':');
    const bodyTxt = rest.join(':').trim();
    // ✗ 마커 원 (빨강)
    s.addShape('ellipse', { x: leftX + 0.20, y: by + 0.04, w: 0.26, h: 0.26,
      fill: { color: 'C0392B' }, line: { type: 'none' } });
    s.addText('✕', { x: leftX + 0.20, y: by + 0.04, w: 0.26, h: 0.26,
      fontFace: F, fontSize: 9, bold: true, color: 'FFFFFF',
      align: 'center', valign: 'middle' });
    if (bodyTxt) {
      s.addText(head.trim(), { x: leftX + 0.54, y: by, w: leftW - 0.68, h: 0.28,
        fontFace: FH, fontSize: 10, bold: true, color: '222222',
        align: 'left', valign: 'middle' });
      s.addText(bodyTxt, { x: leftX + 0.54, y: by + 0.26, w: leftW - 0.68, h: bRowH - 0.30,
        fontFace: F, fontSize: 8.5, color: '666666',
        align: 'left', valign: 'top', lineSpacingMultiple: 1.15 });
    } else {
      s.addText(head.trim(), { x: leftX + 0.54, y: by, w: leftW - 0.68, h: bRowH - 0.08,
        fontFace: F, fontSize: 9.5, color: '444444',
        align: 'left', valign: 'middle', lineSpacingMultiple: 1.15 });
    }
  });

  // ── 오른쪽 패널 (TO-BE: primary 컬러 → 회사 해결책이 돋보이도록) ──
  const isRightLight = _pm_light('#' + C.primary);
  s.addShape('roundRect', { x: rightX, y: cY, w: rightW, h: cH,
    fill: { color: C.primary }, line: { type: 'none' }, rectRadius: 0.18,
    shadow: PM_CARD_SHADOW });

  // 오른쪽 라벨 칩 (흰색 반투명)
  s.addShape('roundRect', { x: rightX + chipPad, y: cY + 0.24, w: rightW - chipPad * 2, h: chipH,
    fill: { color: 'FFFFFF', transparency: 75 }, line: { type: 'none' }, rectRadius: chipH / 2 });
  s.addText(aLabel, { x: rightX + chipPad, y: cY + 0.24, w: rightW - chipPad * 2, h: chipH,
    fontFace: FH, fontSize: 11, bold: true,
    color: isRightLight ? C.textPrimary : 'FFFFFF',
    align: 'center', valign: 'middle', charSpacing: 2 });

  // 오른쪽 불릿 (✓ + 텍스트)
  const aBulletY0 = cY + 0.70;
  aPts.forEach((pt, i) => {
    const ay = aBulletY0 + bRowH * i;
    const [head, ...rest] = pt.split(':');
    const bodyTxt = rest.join(':').trim();
    const txtClr = isRightLight ? C.textPrimary : 'FFFFFF';
    const subClr = isRightLight ? C.textSecondary : 'FFFFFFB0';
    // ✓ 마커 원 (흰색 반투명)
    s.addShape('ellipse', { x: rightX + 0.20, y: ay + 0.04, w: 0.26, h: 0.26,
      fill: { color: 'FFFFFF', transparency: 30 }, line: { type: 'none' } });
    s.addText('✓', { x: rightX + 0.20, y: ay + 0.04, w: 0.26, h: 0.26,
      fontFace: F, fontSize: 9, bold: true,
      color: isRightLight ? C.primary : 'FFFFFF',
      align: 'center', valign: 'middle' });
    // 핵심어 + 설명
    if (bodyTxt) {
      s.addText(head.trim(), { x: rightX + 0.54, y: ay, w: rightW - 0.68, h: 0.28,
        fontFace: FH, fontSize: 10, bold: true, color: txtClr,
        align: 'left', valign: 'middle' });
      s.addText(bodyTxt, { x: rightX + 0.54, y: ay + 0.26, w: rightW - 0.68, h: bRowH - 0.30,
        fontFace: F, fontSize: 8.5, color: isRightLight ? C.textSecondary : 'E8F0FF',
        align: 'left', valign: 'top', lineSpacingMultiple: 1.15 });
    } else {
      s.addText(head.trim(), { x: rightX + 0.54, y: ay, w: rightW - 0.68, h: bRowH - 0.08,
        fontFace: F, fontSize: 9.5, color: isRightLight ? C.textSecondary : 'E8F0FF',
        align: 'left', valign: 'middle', lineSpacingMultiple: 1.15 });
    }
  });

  // ── 중앙 → 화살표 (G-1: 큰 primary 원형 + 그림자) ──
  const arrD = 0.62;
  s.addShape('ellipse', { x: arrowCX - arrD / 2, y: cY + cH / 2 - arrD / 2, w: arrD, h: arrD,
    fill: { color: C.primary }, line: { type: 'none' },
    shadow: PM_CARD_SHADOW });
  s.addText('→', { x: arrowCX - arrD / 2, y: cY + cH / 2 - arrD / 2, w: arrD, h: arrD,
    fontFace: FD, fontSize: 24, bold: true, color: C.textOnPrimary,
    align: 'center', valign: 'middle' });

  // ── 오른쪽 하단: 브랜드 강조 ──
  if (slide.brand_name || (slide._brand && slide._brand.name)) {
    const bName = slide.brand_name || slide._brand.name;
    const bNameW = 3.0;
    s.addText(bName, {
      x: rightX + rightW - bNameW - 0.16, y: cY + cH - 0.38,
      w: bNameW, h: 0.32,
      fontFace: FH, fontSize: 10, bold: true,
      color: isRightLight ? C.primary : 'FFFFFF',
      align: 'right', valign: 'middle', transparency: 30
    });
  }
}

// ── G-1: 체크리스트 pill 레이아웃 (Brandlogy 참고 — 둥근 테두리 pill + 체크 아이콘) ──
function pm_addChecklistPills(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const aX = 0.533, aW = W - aX - 0.28;
  const N = Math.min(items.length, 6);
  if (N === 0) return;

  // 사용 가능 영역 전체를 N등분 (하단 여백 최소화)
  const startY = divY + 0.28;
  const availH = H - startY - 0.50;
  const gap = 0.22;   // 카드 간 시각 분리 강화
  const cardH = (availH - gap * (N - 1)) / N;
  const r = 0.14;

  items.slice(0, N).forEach((item, i) => {
    const cy = startY + i * (cardH + gap);
    const text = (typeof item === 'string' ? item : (item.text || item.heading || '')).replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '');

    // "→" 기준으로 방법론/성과 분리
    const arrowIdx = text.indexOf('→');
    const approach = arrowIdx > 0 ? text.slice(0, arrowIdx).trim() : text;
    const result   = arrowIdx > 0 ? text.slice(arrowIdx + 1).trim() : '';

    // 카드 배경 (흰 roundRect + 테두리)
    s.addShape('roundRect', { x: aX, y: cy, w: aW, h: cardH,
      fill: { color: 'FFFFFF' }, line: { color: C.lineColor, width: 0.5 },
      rectRadius: r });
    // 좌측 accent 바 (개별 카드 느낌 강화)
    s.addShape('rect', { x: aX, y: cy + r, w: 0.05, h: cardH - r * 2,
      fill: { color: C.primary }, line: { type: 'none' } });

    // 좌측 번호 박스 (큰 roundRect + 번호) — 아이콘 대신 사례 번호
    const boxSz = Math.min(cardH * 0.70, 0.88);
    const boxY = cy + (cardH - boxSz) / 2;
    pm_addIconBox(s, C, fonts, aX + 0.18, boxY, boxSz, null, i);

    // 텍스트 영역 (번호 박스 우측)
    const txtX = aX + 0.18 + boxSz + 0.22;
    const txtW = aW - (txtX - aX) - 0.18;

    if (result) {
      // 방법론(볼드) + 성과(보라) — 위아래 여백 균등
      s.addText(approach, { x: txtX, y: cy + cardH * 0.12, w: txtW, h: cardH * 0.42,
        fontFace: FH, fontSize: 14, bold: true, color: C.textPrimary,
        align: 'left', valign: 'middle', wrap: true, lineSpacingMultiple: 1.2 });
      s.addText(result, { x: txtX, y: cy + cardH * 0.52, w: txtW, h: cardH * 0.36,
        fontFace: F, fontSize: 11, color: C.primary,
        align: 'left', valign: 'middle', wrap: true, lineSpacingMultiple: 1.15 });
    } else {
      s.addText(approach, { x: txtX, y: cy, w: txtW, h: cardH,
        fontFace: FH, fontSize: 14, color: C.textPrimary,
        align: 'left', valign: 'middle', wrap: true, lineSpacingMultiple: 1.25 });
    }
  });
}

// ── G-1: Asymmetric 1+3 레이아웃 (좌 대형 카드 + 우 3스택) ──
function pm_addAsymmetric1_3(s, C, fonts, title, items, eyebrow) {
  const {F, FH, FD} = _ff(fonts);
  const divY = pm_addSlideFrame(s, C, fonts, title, eyebrow || '');
  const N = Math.min(items.length, 4);
  if (N === 0) return;

  const aX = 0.533, aW = W - aX - 0.28;
  const aY = divY + 0.22, aH = H - aY - 0.55;
  const GAP = 0.16;
  const leftW = aW * 0.52;
  const rightW = aW - leftW - GAP;
  const rightCardH = (aH - GAP * 2) / 3;
  const r = 0.14;

  // 좌 대형 카드
  const item0 = items[0] || '';
  const p0 = parseIconItem(typeof item0 === 'string' ? item0 : (item0.heading || ''));
  const ci0 = p0.text.indexOf(':');
  const h0 = ci0 > 0 ? p0.text.slice(0, ci0).trim() : p0.text.slice(0, 30);
  const b0 = ci0 > 0 ? p0.text.slice(ci0 + 1).trim() : '';

  s.addShape('roundRect', { x: aX, y: aY, w: leftW, h: aH,
    fill: { color: 'FFFFFF' }, line: { color: C.lineColor, width: 0.5 },
    rectRadius: r, shadow: PM_CARD_SHADOW });
  // 상단 accent 바
  s.addShape('roundRect', { x: aX, y: aY, w: leftW, h: 0.10,
    fill: { color: C.primary }, line: { type: 'none' }, rectRadius: r * 0.5 });
  // 아이콘/번호
  const bxSz = Math.min(leftW * 0.20, 0.80);
  pm_addIconBox(s, C, fonts, aX + (leftW - bxSz) / 2, aY + 0.30, bxSz, p0.icon, 0);
  // 헤딩
  s.addText(h0, { x: aX + 0.20, y: aY + 0.30 + bxSz + 0.24, w: leftW - 0.40, h: 0.48,
    fontFace: FH, fontSize: 16, bold: true, color: C.primary,
    align: 'center', valign: 'middle', wrap: true });
  // 본문
  if (b0) s.addText(b0, { x: aX + 0.20, y: aY + 0.30 + bxSz + 0.78, w: leftW - 0.40, h: aH - bxSz - 1.50,
    fontFace: F, fontSize: 12, color: C.textSecondary,
    align: 'center', valign: 'top', wrap: true, lineSpacingMultiple: 1.4 });

  // 우 3스택 카드
  for (let i = 1; i < Math.min(N, 4); i++) {
    const item = items[i] || '';
    const p = parseIconItem(typeof item === 'string' ? item : (item.heading || ''));
    const ci = p.text.indexOf(':');
    const head = ci > 0 ? p.text.slice(0, ci).trim() : p.text.slice(0, 30);
    const body = ci > 0 ? p.text.slice(ci + 1).trim() : '';
    const ry = aY + (i - 1) * (rightCardH + GAP);
    const rx = aX + leftW + GAP;

    s.addShape('roundRect', { x: rx, y: ry, w: rightW, h: rightCardH,
      fill: { color: 'FFFFFF' }, line: { color: C.lineColor, width: 0.5 },
      rectRadius: r, shadow: PM_CARD_SHADOW });
    // 좌측 번호 pill
    const numW = 0.40, numH = 0.28;
    s.addShape('roundRect', { x: rx + 0.14, y: ry + 0.14, w: numW, h: numH,
      fill: { color: C.primary }, line: { type: 'none' }, rectRadius: numH / 2 });
    s.addText(String(i + 1).padStart(2, '0'), { x: rx + 0.14, y: ry + 0.14, w: numW, h: numH,
      fontFace: FH, fontSize: 9, bold: true, color: C.textOnPrimary,
      align: 'center', valign: 'middle' });
    // 헤딩
    s.addText(head, { x: rx + 0.62, y: ry + 0.10, w: rightW - 0.76, h: 0.36,
      fontFace: FH, fontSize: 12, bold: true, color: C.primary,
      align: 'left', valign: 'middle', wrap: true });
    // 본문
    if (body) s.addText(body, { x: rx + 0.14, y: ry + 0.50, w: rightW - 0.28, h: rightCardH - 0.60,
      fontFace: F, fontSize: 10.5, color: C.textSecondary,
      align: 'left', valign: 'top', wrap: true, lineSpacingMultiple: 1.3 });
  }
}

  async function generateAndDownloadPPTX(data) {
    const pptx = new PptxGenJS();
    pptx.defineLayout({ name: 'PPTMON_WIDE', width: 13.3333, height: 7.5 });
    pptx.layout = 'PPTMON_WIDE';

    // ── Font system: F(본문) / FH(헤딩) / FD(디스플레이) ──────────────────
    const _fontCategory = (data.brand?.fontCategory || 'sans').toLowerCase();
    let fonts = { F: '맑은 고딕', FH: '맑은 고딕', FD: '맑은 고딕' };
    const _pptxFontEl = document.getElementById('pptx-font-info');
    try {
      // 항상 로드: Pretendard 3종 (Regular·Bold·ExtraBold)
      const [fontReg, fontBold, fontXB] = await Promise.all([
        _loadFontB64(_PRETENDARD_BASE + 'Pretendard-Regular.otf'),
        _loadFontB64(_PRETENDARD_BASE + 'Pretendard-Bold.otf'),
        _loadFontB64(_PRETENDARD_BASE + 'Pretendard-ExtraBold.otf'),
      ]);
      if (fontReg && fontBold) {
        pptx.defineFontFace({ name: 'Pretendard',    data: fontReg,  type: 'Regular' });
        pptx.defineFontFace({ name: 'Pretendard',    data: fontBold, type: 'Bold' });
        fonts.F = 'Pretendard';
      }
      if (fontXB) {
        // Pretendard-XB: Regular+Bold 모두 ExtraBold 데이터 → bold:true/false 모두 동작
        pptx.defineFontFace({ name: 'Pretendard-XB', data: fontXB, type: 'Regular' });
        pptx.defineFontFace({ name: 'Pretendard-XB', data: fontXB, type: 'Bold' });
      }

      if (_fontCategory === 'serif') {
        const [nsReg, nsBold] = await Promise.all([
          _loadFontB64(_NOTO_SERIF_BASE + 'noto-serif-kr-korean-400-normal.woff2'),
          _loadFontB64(_NOTO_SERIF_BASE + 'noto-serif-kr-korean-700-normal.woff2'),
        ]);
        if (nsReg && nsBold) {
          pptx.defineFontFace({ name: 'NotoSerifKR', data: nsReg,  type: 'Regular' });
          pptx.defineFontFace({ name: 'NotoSerifKR', data: nsBold, type: 'Bold' });
          fonts.FH = fonts.FD = 'NotoSerifKR';
        } else { fonts.FH = fonts.FD = fontXB ? 'Pretendard-XB' : fonts.F; }

      } else if (_fontCategory === 'display') {
        const bhsReg = await _loadFontB64(_BHS_BASE + 'black-han-sans-korean-400-normal.woff2');
        if (bhsReg) {
          pptx.defineFontFace({ name: 'BlackHanSans', data: bhsReg, type: 'Regular' });
          pptx.defineFontFace({ name: 'BlackHanSans', data: bhsReg, type: 'Bold' });
          fonts.FH = fonts.FD = 'BlackHanSans';
        } else { fonts.FH = fonts.FD = fontXB ? 'Pretendard-XB' : fonts.F; }

      } else {
        fonts.FH = fonts.FD = fontXB ? 'Pretendard-XB' : fonts.F;
      }

      const catLabel = _fontCategory === 'serif' ? fonts.FH :
                       _fontCategory === 'display' ? fonts.FH : 'Pretendard-XB';
      if (_pptxFontEl) _pptxFontEl.textContent = `폰트: ${fonts.F} + ${catLabel} (PPTX 내장)`;
    } catch(e) {
      if (_pptxFontEl) _pptxFontEl.textContent = '폰트: 맑은 고딕 (fallback)';
    }

    // W, H는 상위 스코프 상수 사용 (13.3333, 7.5)
    const brand       = data.brand  || {};
    const slides      = data.slides || [];
    const meta        = data.meta   || {};
    const accentHex   = (brand.primaryColor || '#1C3D5A').replace('#','');
    const companyName = brand.name    || '';
    const logoB64     = brand.logoB64  || '';
    const logoMime    = brand.logoMime || 'png';
    const showLogo    = !!(logoB64 && logoMime !== 'svg+xml');
    const faviconB64  = brand.faviconB64  || logoB64;
    const faviconMime = brand.faviconMime || logoMime;
    const showFavicon = !!(faviconB64 && faviconMime !== 'svg+xml');
    // 아티스트 전용 아이콘 (page_subject_icon — C-type 우상단 배치)
    const subjIconB64  = brand.pageSubjectIconB64  || '';
    const subjIconMime = brand.pageSubjectIconMime || 'png';
    const showSubjIcon = !!(subjIconB64 && subjIconMime !== 'svg+xml');
    // 내러티브 타입별 배경 팔레트
    const narrativeType = (meta.narrative_type || brand.narrative_type || 'A').toUpperCase();
    const NT_PPTMON_BG  = { A:'F5F5F8', B:'F5F5F8', C:'F5F5F8', D:'F5F5F8' };
    const NT_BG_DARK    = { A:'111827', B:'1A2F4A', C:'2D1F3D', D:'0F0F0F' };
    // 사이트 밝은 배경색이 있으면 슬라이드 배경에 반영 (크림/파스텔 느낌)
    const _siteLightBg = (brand.siteLightBg || '').replace('#', '');
    const pmBg   = _siteLightBg || NT_PPTMON_BG[narrativeType] || 'F8F9FA';
    const bgDark = NT_BG_DARK[narrativeType]  || '111827';
    const C       = createColorSystem(accentHex, pmBg);

    // ── 보조 컬러 (Secondary Color) 계산 ──────────────────────────────
    // 1순위: 홈페이지에서 추출한 accent_color (primary와 다를 때만)
    // 2순위: primary에서 hue -30° 자동 계산 (유사 색상 계열)
    const _pm_hue_rotate = (hex, deg) => {
      const rr=parseInt(hex.slice(0,2),16)/255, gg=parseInt(hex.slice(2,4),16)/255, bb=parseInt(hex.slice(4,6),16)/255;
      const mx=Math.max(rr,gg,bb), mn=Math.min(rr,gg,bb); let h,s; const l=(mx+mn)/2;
      if(mx===mn){h=s=0;}else{const d=mx-mn;s=l>.5?d/(2-mx-mn):d/(mx+mn);
        h=(mx===rr?(gg-bb)/d+(gg<bb?6:0):mx===gg?(bb-rr)/d+2:(rr-gg)/d+4)/6;}
      h=(h+deg/360+10)%1;
      const h2r=(p,q,t)=>{t=(t+1)%1;return t<1/6?p+(q-p)*6*t:t<1/2?q:t<2/3?p+(q-p)*(2/3-t)*6:p;};
      const q2=l<.5?l*(1+s):l+s-l*s,p2=2*l-q2;
      return [h2r(p2,q2,h+1/3),h2r(p2,q2,h),h2r(p2,q2,h-1/3)].map(x=>Math.round(x*255).toString(16).padStart(2,'0')).join('');
    };
    const _metaAccent2 = ((meta.accent_color2||'').replace('#','')).toUpperCase();
    const _metaAccent  = ((meta.accent_color ||'').replace('#','')).toUpperCase();
    const _primaryHex  = accentHex.toUpperCase();
    // C2: 포인트 악센트 — 우선순위: accent_color2(두 번째 브랜드 컬러) → primary 25% 밝게 (hue-rotate 금지: 엉뚱한 색 생성 위험)
    const C2 = (_metaAccent2 && _metaAccent2.length === 6)
      ? _metaAccent2
      : _pm_bright(accentHex, 0.25);  // primary 계열 유지

    // 커버 배경 우선순위: siteDarkBg(실제 사이트 어두운 배경) → primary 기반 very dark → 기본값
    const _siteDarkBg = (brand.siteDarkBg || '').replace('#', '');
    const _primaryDark = _pm_bright('#' + accentHex, -0.85).replace('#', '');  // primary에서 85% 어둡게
    const coverBg = _siteDarkBg || _primaryDark || '111111';
    // isDarkSite: 다크 배경 사이트 → C.primary=dark, C2=vibrant
    // isMonochrome: 흰검 지배형 → C.primary=#111, C2=포인트 vibrant (아주 조금만 사용)
    // 두 경우 모두 _hiColor = C2 → eyebrow pill/cover accent bar에만 소량 적용
    const isDarkSite   = !!(brand.isDarkSite);
    const isMonochrome = !!(brand.isMonochrome);
    const _hiColor = (isDarkSite || isMonochrome) ? C2 : C.primary;
    C.eyebrowFill  = _hiColor;  // pm_addSlideFrame 등 모든 eyebrow pill에 주입

    pptx.title   = companyName || 'Slides';
    pptx.author  = 'TickDeck';
    pptx.company = 'TickDeck';
    pptx.subject = 'Generated by TickDeck AI';

    // 로고 원본 비율 계산 (절대 원칙: 비율 보존)
    let logoAspect = 0;
    if (showLogo) {
      logoAspect = await new Promise(res => {
        const img = new Image();
        img.onload  = () => res(img.naturalWidth / (img.naturalHeight || 1));
        img.onerror = () => res(2.5);
        img.src = `data:image/${logoMime};base64,${logoB64}`;
      });
    }

    let splitIdx = 0, cardFlipIdx = 0, portfolioFlipIdx = 0, prevLayout = '', pptxLayoutCount = {}, pptxSectionCounter = 0;
    const usedImgSet = new Set();

    for (const [i, slide] of slides.entries()) {
      const s           = pptx.addSlide();
      const isLastSlide = (i === slides.length - 1);
      const stype  = slide.type || '';
      const {F, FH, FD} = _ff(fonts);
      const _stripIcon = t => String(t||'').replace(/^\[[\w-]+\]\s*/, '');
      const hl     = _stripIcon(slide.headline    || '');
      const sub    = _stripIcon(slide.subheadline || '');
      const _rawBody = Array.isArray(slide.body) ? slide.body.filter(b => b && b.trim()) : [];
      const body   = _rawBody.length > 0 ? _rawBody : (sub ? [sub] : []);
      const bgB64    = slide.bg_b64    || '';
      const bgMime   = slide.bg_mime   || 'png';
      const bgAspect = slide.bg_aspect || 1.0;
      const op     = slide.overlay_opacity != null ? slide.overlay_opacity : 0.65;
      const overlayT = Math.round((1 - op) * 100);
      let layout  = getSlideLayout(slide, narrativeType, prevLayout, pptxLayoutCount);
      // 이미지 없는 split/portfolio → 다양한 레이아웃으로 분산 (워터마크/빈 패널 방지)
      if ((layout === 'split' || layout === 'portfolio') && !bgB64) {
        const _bodyN = (slide.body || []).length;
        if (_bodyN >= 4) layout = 'two_col_text';
        else if (_bodyN >= 2) layout = 'cards';
        else layout = 'cards';
      }
      // section은 시각적 구분자 — 연속 방지 카운터에 영향 안 줌
      if (!['cover','cta','toc','section'].includes(layout)) {
        prevLayout = layout;
        pptxLayoutCount[layout] = (pptxLayoutCount[layout] || 0) + 1;
      }
      // eyebrow: slide 자체 필드 > stype 변환 (통일된 헤더 라벨)
      const _rawEyebrow = slide.eyebrow || slide.section_label || stype.replace(/_\d+$/,'').replace(/_/g,' ');
      const eyebrow = _rawEyebrow.toUpperCase();
      // imgKey: 길이 + 앞500 + 뒤200 조합 — JPEG/PNG가 동일 해상도로 헤더 200자 동일해도 구별 가능
      const imgKey  = bgB64 ? `${bgB64.length}:${bgB64.slice(0, 500)}${bgB64.slice(-200)}` : '';
      // dedup은 split/cards 레이아웃에만 적용 — portfolio/cover/pptmon은 항상 이미지 허용
      const deduplicatable = ['split', 'cards'].includes(layout);
      const isImgDup = deduplicatable && imgKey && usedImgSet.has(imgKey);
      if (deduplicatable && imgKey && !isImgDup) usedImgSet.add(imgKey);
      const bgData  = (bgB64 && !isImgDup) ? `data:image/${bgMime};base64,${bgB64}` : null;

      // ── visual_style 기반 배경 / 텍스트 색상 ──
      const vs   = slide.visual_style || {};
      const isLight       = (vs.bg_style === 'solid_light');
      const pptxTextColor = isLight ? '1A1A1A' : 'FFFFFF';

      // cards: right(짝수) / left(홀수) / center(이미지 없음) 교차
      const cardMode  = layout === 'cards'     ? (!bgData ? 'center' : cardFlipIdx     % 2 === 0 ? 'right' : 'left') : 'right';
      const portMode  = layout === 'portfolio' ? (portfolioFlipIdx % 2 === 0 ? 'left' : 'right') : 'left';
      if (layout === 'cards')     cardFlipIdx++;
      if (layout === 'portfolio') portfolioFlipIdx++;
      if (layout === 'section')   pptxSectionCounter++;

      // ── 공통 헬퍼 ──────────────────────────────────
      const addFullBg = () => {
        if (!bgData) {
          // typography 모드: visual_style 기반 단색 배경
          // (PPTX는 CSS 그라디언트 미지원 → 단색이 오히려 깔끔)
          const _bgBase  = (vs.bg_base  || '#0F0F0F').replace('#', '');
          const _bgColor = (vs.bg_color || '#1C3D5A').replace('#', '');
          const _bst     = vs.bg_style || 'solid_dark';
          if (_bst === 'solid_light') {
            s.background = { color: 'F5F5F5' };
          } else if (_bst === 'gradient_bold') {
            s.background = { color: _bgColor };
          } else {
            s.background = { color: _bgBase };
          }
          return;
        }
        // contain 방식: 비율 유지, 짤림 없이 최대 크기, 여백은 near-black
        const slideAspect = W / H;  // 13.33/7.5 ≈ 1.777
        s.background = { color: '111111' };
        if (bgAspect >= slideAspect) {
          // 가로형(슬라이드보다 넓음): 너비를 W에 맞추고 상하 중앙 정렬 (상하 바)
          const iW = W, iH = W / bgAspect;
          const iY = (H - iH) / 2;
          s.addImage({ data: bgData, x: 0, y: iY, w: iW, h: iH });
        } else {
          // 세로형(슬라이드보다 좁음): 높이를 H에 맞추고 좌우 중앙 정렬 (좌우 바)
          const iH = H, iW = H * bgAspect;
          const iX = (W - iW) / 2;
          s.addImage({ data: bgData, x: iX, y: 0, w: iW, h: iH });
        }
      };
      const addOverlay = (t) => {
        s.addShape('rect', { x: 0, y: 0, w: W, h: H,
          fill: { color: '000000', transparency: t }, line: { type: 'none' } });
      };
      // 로고: 원본 비율 절대 보존 (maxW × maxH 박스 내 비율 유지 배치)
      const addLogo = (x, y, maxW = 1.8, maxH = 0.5) => {
        if (!showLogo || !logoAspect) return;
        if (!logoB64 || logoB64.length < 300) return;
        // 세로형(< 1.0) 또는 극단적 가로형(> 4.0)은 로고 오감지 → 스킵
        if (logoAspect < 1.0 || logoAspect > 4.0) return;
        let lW, lH;
        if (logoAspect >= maxW / maxH) { lW = maxW; lH = maxW / logoAspect; }
        else { lH = maxH; lW = maxH * logoAspect; }
        s.addImage({ data: `data:image/${logoMime};base64,${logoB64}`,
                     x, y, w: lW, h: lH });
      };
      const addPageNum = (clr) => {
        s.addText(`${i + 1} / ${slides.length}`, {
          x: W - 1.1, y: H - 0.45, w: 0.9, h: 0.3,
          fontSize: 9, color: clr || C.textMuted, align: 'right', fontFace: F });
      };
      const addFavicon = () => {
        if (isLastSlide) return;
        // C-type: subjectIcon 우선 (커버 포함 모든 슬라이드), 없으면 일반 favicon (커버 제외)
        if (narrativeType === 'C' && showSubjIcon) {
          if (subjIconB64 && subjIconB64.length > 300) {
            // sizing 없이 고정 크기 — contain 버그 방지, 정사각형 아이콘 가정
            s.addImage({ data: `data:image/${subjIconMime};base64,${subjIconB64}`,
                         x: W - 0.56, y: 0.10, w: 0.38, h: 0.38, transparency: 10 });
          }
        } else if (showFavicon && stype !== 'cover') {
          if (faviconB64 && faviconB64.length > 300) {
            // 원본 비율 유지 — contain으로 박스 내 맞춤
            s.addImage({ data: `data:image/${faviconMime};base64,${faviconB64}`,
                         x: W - 0.56, y: 0.10, w: 0.42, h: 0.42,
                         sizing: { type: 'contain', w: 0.42, h: 0.42 } });
          }
        }
      };
      let _cpDone = false;
      const addCopyright = (clr, cpX) => {
        if (!companyName) return;
        _cpDone = true;
        s.addText(`© ${new Date().getFullYear()} ${companyName}. All Rights Reserved.`, {
          x: cpX !== undefined ? cpX : 0.48, y: H - 0.4, w: 6, h: 0.28,
          fontSize: 8, color: clr || C.textMuted, fontFace: F });
      };
      // PPTMON 상단/하단 수평 액센트 라인
      const addAccentLines = () => {
        s.addShape('rect', { x: 0, y: 0, w: W, h: 0.07,
          fill: { color: C.primary }, line: { type: 'none' } });
        s.addShape('rect', { x: 0, y: H - 0.07, w: W, h: 0.07,
          fill: { color: C.primary }, line: { type: 'none' } });
        s.addShape('rect', { x: 0, y: 0, w: 0.055, h: H,
          fill: { color: C.primary }, line: { type: 'none' } });
      };

      // ════════════════════════════════════════════════
      if (layout === 'cover') {
        // ── Typography-first Cover (이미지 없음, narrative_type별 듀얼 컬러) ──
        const NT = narrativeType;

        if (NT === 'C') {
          if (bgData) {
            // IMAGE-FIRST 커버: 비율 유지 cover 방식 (왜곡 없이 슬라이드 전체 덮음)
            addFullBg();
            // 전체 어두운 오버레이 (기본 가독성)
            s.addShape('rect', { x: 0, y: 0, w: W, h: H,
              fill: { color: '000000', transparency: 40 }, line: { type: 'none' } });
            // 좌측 추가 어둠 (텍스트 영역 가독성 강화)
            s.addShape('rect', { x: 0, y: 0, w: W * 0.65, h: H,
              fill: { color: '000000', transparency: 30 }, line: { type: 'none' } });
            // 좌상단 eyebrow 배지 (흰 배경 + 어두운 텍스트 — 어두운 커버에서 선명하게)
            s.addShape('rect', { x: W * 0.06, y: H * 0.10, w: W * 0.18, h: 0.28,
              fill: { color: 'FFFFFF' }, line: { type: 'none' }, rectRadius: 0.04 });
            s.addText((companyName || '').toUpperCase(), {
              x: W * 0.06, y: H * 0.10, w: W * 0.18, h: 0.28,
              fontSize: 9, bold: true, color: '1A1A1A', charSpacing: 3,
              align: 'center', valign: 'middle', fontFace: F });
            // 헤드라인
            const _cImgHlFs = (hl||'').length > 28 ? 46 : (hl||'').length > 18 ? 54 : 62;
            s.addText(hl, { x: W * 0.06, y: H * 0.22, w: W * 0.58, h: H * 0.52,
              fontSize: _cImgHlFs, bold: true, color: 'FFFFFF', wrap: true,
              align: 'left', valign: 'middle', lineSpacingMultiple: 1.15, fontFace: FD });
            // sub
            if (sub) s.addText(sub, { x: W * 0.06, y: H * 0.76, w: W * 0.58, h: H * 0.14,
              fontSize: 14, color: 'EEEEEE', align: 'left', valign: 'top', fontFace: F, wrap: true });
            // 하단 primary 액센트 바
            s.addShape('rect', { x: 0, y: H - 0.05, w: W * 0.32, h: 0.05,
              fill: { color: C.primary }, line: { type: 'none' } });
            addLogo(W * 0.06, H * 0.86, 1.8, 0.40);
            addFavicon();
            addCopyright('CCCCCC');
            addPageNum('FFFFFF');
          } else {
            // TEXT-FIRST 커버 (이미지 없을 때): 다크 풀배경 + 타이포 임팩트
            s.background = { color: coverBg };
            // 우상단 대형 데코 원 (primary, 반투명) — 시각적 임팩트
            s.addShape('ellipse', { x: W * 0.52, y: -H * 0.30, w: H * 1.15, h: H * 1.15,
              fill: { color: C.primary, transparency: 78 }, line: { type: 'none' } });
            // 우하단 소형 데코 원 — 레이어 깊이감
            s.addShape('ellipse', { x: W * 0.82, y: H * 0.62, w: H * 0.55, h: H * 0.55,
              fill: { color: C.primary, transparency: 88 }, line: { type: 'none' } });
            // 좌측 굵은 primary bar
            s.addShape('rect', { x: 0, y: 0, w: W * 0.028, h: H,
              fill: { color: C.primary }, line: { type: 'none' } });
            // 상단 primary band
            s.addShape('rect', { x: 0, y: 0, w: W, h: H * 0.012,
              fill: { color: C.primary }, line: { type: 'none' } });
            // 회사명 소형 배지 (자간 넓게)
            if (companyName) s.addText(companyName.toUpperCase(), {
              x: W * 0.07, y: H * 0.13, w: W * 0.60, h: 0.40,
              fontSize: 11, bold: true, color: 'FFFFFF', charSpacing: 5,
              align: 'left', valign: 'middle', fontFace: F });
            // 헤드라인 (대형, 흰색) — 길이별 동적 사이즈
            const _cHlFs2 = (hl||'').length > 28 ? 46 : (hl||'').length > 18 ? 54 : 64;
            s.addText(hl, { x: W * 0.07, y: H * 0.22, w: W * 0.76, h: H * 0.46,
              fontSize: _cHlFs2, bold: true, color: 'FFFFFF', wrap: true,
              align: 'left', valign: 'middle', lineSpacingMultiple: 1.15, fontFace: FD });
            // 헤드라인 아래 horizontal accent line
            s.addShape('rect', { x: W * 0.07, y: H * 0.72, w: W * 0.14, h: 0.04,
              fill: { color: C.primary }, line: { type: 'none' } });
            // 서브헤드라인
            if (sub) s.addText(sub, { x: W * 0.07, y: H * 0.75, w: W * 0.72, h: H * 0.12,
              fontSize: 18, color: 'CCCCCC', align: 'left', valign: 'top', fontFace: F, wrap: true });
            // 하단 primary full-width bar
            s.addShape('rect', { x: 0, y: H - 0.06, w: W, h: 0.06,
              fill: { color: C.primary }, line: { type: 'none' } });
            addLogo(W * 0.07, H * 0.87, 1.80, 0.42);
            addFavicon();
            addCopyright('888888');
            addPageNum('FFFFFF');
          }

        } else if (NT === 'F') {
          // Education: 흰 배경 + 좌 두꺼운 primary bar + secondary 상단 선
          s.background = { color: 'FAFAFA' };
          s.addShape('rect', { x: 0, y: 0, w: W * 0.030, h: H,
            fill: { color: C.primary }, line: { type: 'none' } });
          s.addShape('rect', { x: 0, y: 0, w: W, h: W * 0.006,
            fill: { color: C.accentLight }, line: { type: 'none' } });
          s.addShape('rect', { x: 0, y: H - 0.06, w: W, h: 0.06,
            fill: { color: C.primary }, line: { type: 'none' } });
          if (companyName) s.addText(companyName.toUpperCase(), {
            x: W * 0.07, y: H * 0.14, w: W * 0.80, h: H * 0.10,
            fontSize: 12, color: C.textSecondary, charSpacing: 4,
            align: 'left', valign: 'middle', fontFace: F });
          s.addShape('rect', { x: W * 0.07, y: H * 0.28, w: W * 0.44, h: 0.04,
            fill: { color: C.primary }, line: { type: 'none' } });
          s.addText(hl, { x: W * 0.07, y: H * 0.31, w: W * 0.78, h: H * 0.32,
            fontSize: 40, bold: true, color: C.textPrimary, wrap: true,
            align: 'left', valign: 'top', lineSpacingMultiple: 1.2, fontFace: FD });
          if (sub) s.addText(sub, { x: W * 0.07, y: H * 0.66, w: W * 0.78, h: H * 0.12,
            fontSize: 17, color: C.primary, fontFace: F, wrap: true });

        } else {
          // A (default) / B / D: config-based 통합 렌더
          const _cv = ({
            B: {
              bg: coverBg || '08080E',   circTr: 94, wmarkTr: 93, bottomH: 0.06,
              coClr: 'AAAAAA', coSp: 5,  coFs: 12, coY: H * 0.13,
              divSingleY: H * 0.25,      hlBold: true, hlFsAdj: 0, hlY: H * 0.27, hlLSM: 1.12,
              accentLine: true, subFs: 20, hlFont: FH,
              logo: [W * 0.76, H * 0.015, 2.4, 0.52],
              logoFb: { x: W * 0.74, y: H * 0.015, w: W * 0.22, h: 0.46, clr: 'FFFFFF', bold: true }
            },
            D: {
              bg: coverBg || '07070D',   circTr: 97, wmarkTr: 96, bottomH: 0.03,
              coClr: '666666', coSp: 9,  coFs: 11, coY: H * 0.14,
              divSingleY: H * 0.26,      hlBold: false, hlFsAdj: -6, hlY: H * 0.30, hlLSM: 1.30,
              accentLine: false, subFs: 16, hlFont: FH,
              logo: [W * 0.44, H * 0.76, 1.60, 0.50],
              logoFb: { x: W * 0.42, y: H * 0.76, w: W * 0.20, h: 0.46, clr: C.accentLight, bold: false }
            }
          })[NT] || {
            bg: coverBg,               circTr: 92, wmarkTr: 91, bottomH: 0.06,
            coClr: 'BBBBBB', coSp: 6,  coFs: 13, coY: H * 0.14,
            divSingleY: H * 0.26,      hlBold: true, hlFsAdj: 0, hlY: H * 0.28, hlLSM: 1.12,
            accentLine: true, subFs: 20, hlFont: FD,
            logo: null, logoFb: null
          };
          // 사이트 대표 이미지: s.background 속성 사용 (sizing:cover stretch 버그 방지)
          if (bgData) {
            s.background = { data: bgData };
            s.addShape('rect', { x: 0, y: 0, w: W, h: H,
              fill: { color: '000000', transparency: 62 }, line: { type: 'none' } });
          } else {
            // 틴티드 다크 배경 (순수 검정 대신 primary 색조 포함)
            s.background = { color: C.tintedDark || _cv.bg };
          }
          // ── 미니멀 데코 (less is more) ──
          if (NT === 'D') {
            // Luxury: 극세선 테두리만
            s.addShape('rect', { x: 0, y: 0, w: W, h: 0.03, fill: { color: C.primary }, line: { type: 'none' } });
            s.addShape('rect', { x: 0, y: H - 0.03, w: W, h: 0.03, fill: { color: C.primary }, line: { type: 'none' } });
          } else {
            // A / B: 하단 bar + 단일 데코 원만 (좌측 bar, 상단 라인 제거)
            s.addShape('rect', { x: 0, y: H - _cv.bottomH, w: W, h: _cv.bottomH, fill: { color: _hiColor }, line: { type: 'none' } });
            if (NT === 'B') s.addShape('rect', { x: 0, y: 0, w: W, h: H * 0.06, fill: { color: _hiColor }, line: { type: 'none' } });
          }
          // 단일 데코 원 (우측 — 절제된 단 1개)
          const _circD = H * 1.10;
          s.addShape('ellipse', { x: W * 0.60, y: -H * 0.10, w: _circD, h: _circD,
            fill: { color: C.primary, transparency: _cv.circTr }, line: { type: 'none' } });
          // ── 회사명 pill badge (상단) ──
          if (companyName) {
            const _coStr = companyName.toUpperCase();
            const _coLen = _coStr.replace(/[^\x00-\xff]/g, 'xx').length;
            const _coW = Math.min(_coLen * 0.12 + 0.50, 4.0), _coH = 0.30;
            if (NT === 'D') {
              // D-type: 텍스트만 (pill 없이)
              s.addText(_coStr, { x: W * 0.10, y: H * 0.16, w: W * 0.50, h: H * 0.08,
                fontSize: 11, color: C.tintedGray || '666666', charSpacing: _cv.coSp,
                align: 'left', valign: 'middle', fontFace: F });
            } else {
              // A/B: pill badge
              s.addShape('roundRect', { x: W * 0.10, y: H * 0.16, w: _coW, h: _coH,
                fill: { color: C.primary }, line: { type: 'none' }, rectRadius: _coH / 2 });
              s.addText(_coStr, { x: W * 0.10, y: H * 0.16, w: _coW, h: _coH,
                fontSize: 9, bold: true, color: C.textOnPrimary, charSpacing: 2,
                align: 'center', valign: 'middle', fontFace: F });
            }
          }
          // ── 헤드라인 (크기 UP — 더 과감하게) ──
          const _hlLen = (hl || '').length;
          const _baseFs = _hlLen > 28 ? 52 : _hlLen > 18 ? 64 : 80;
          const _hlY = NT === 'D' ? H * 0.28 : H * 0.26;
          s.addText(hl, { x: W * 0.10, y: _hlY, w: W * 0.72, h: H * 0.42,
            fontSize: _baseFs + _cv.hlFsAdj, bold: _cv.hlBold, color: 'FFFFFF', wrap: true,
            shrinkText: true,
            align: 'left', valign: 'top', lineSpacingMultiple: _cv.hlLSM, fontFace: _cv.hlFont || FD });
          // ── short accent line + sub ──
          s.addShape('rect', { x: W * 0.10, y: H * 0.70, w: W * 0.10, h: 0.03,
            fill: { color: C.primary }, line: { type: 'none' } });
          if (sub) s.addText(sub, { x: W * 0.10, y: H * 0.74, w: W * 0.72, h: H * 0.12,
            fontSize: _cv.subFs, color: C.tintedGray || 'AAAAAA', align: 'left', valign: 'top', fontFace: F, wrap: true,
            lineSpacingMultiple: 1.3 });
          // ── 로고 ──
          if (_cv.logo) {
            addLogo(..._cv.logo);
            if (!showLogo && companyName) s.addText(companyName.toUpperCase(), {
              x: _cv.logoFb.x, y: _cv.logoFb.y, w: _cv.logoFb.w, h: _cv.logoFb.h,
              fontSize: 10, bold: _cv.logoFb.bold, color: _cv.logoFb.clr, charSpacing: 3,
              align: 'center', valign: 'middle', fontFace: F });
          }
        } // end cover types

      // ════════════════════════════════════════════════
      } else if (layout === 'toc') {
        // ── TOC: 상단 다크 밴드(40%) + 하단 번호 카드 그리드 (레퍼런스 PPT 기반) ──
        const bandH = H * 0.42;
        s.background = { color: C.bg };

        // 상단 다크 밴드
        s.addShape('rect', { x: 0, y: 0, w: W, h: bandH,
          fill: { color: bgDark }, line: { type: 'none' } });
        // 밴드 상단 accent 바
        s.addShape('rect', { x: 0, y: 0, w: W, h: 0.07,
          fill: { color: C.primary }, line: { type: 'none' } });
        // 밴드 하단 accent 선
        s.addShape('rect', { x: 0, y: bandH - 0.055, w: W, h: 0.055,
          fill: { color: C.primary }, line: { type: 'none' } });

        // 밴드 배경 장식 원
        s.addShape('ellipse', { x: W * 0.68, y: -bandH * 0.35, w: bandH * 1.3, h: bandH * 1.3,
          fill: { color: 'FFFFFF', transparency: 94 }, line: { type: 'none' } });

        // "INDEX" 서브레이블 (밴드 내 상단)
        s.addText('INDEX', {
          x: W * 0.06, y: H * 0.10, w: W * 0.4, h: H * 0.06,
          fontSize: 11, bold: true, color: C.primary,
          charSpacing: 5, valign: 'top', fontFace: F });

        // 메인 타이틀 (밴드 내)
        s.addText(hl || '목차', {
          x: W * 0.06, y: H * 0.16, w: W * 0.55, h: H * 0.20,
          fontSize: 32, bold: true, color: 'FFFFFF',
          wrap: true, shrinkText: true, align: 'left', valign: 'top',
          lineSpacingMultiple: 1.2, fontFace: FH });

        // ── 하단 카드 영역 ──
        const items   = body.length > 0 ? body : [];
        const nCols   = Math.min(Math.max(items.length, 2), 4);
        const cardAreaX = W * 0.04;
        const cardAreaW = W * 0.92;
        const cardGapT  = W * 0.016;
        const cWT = (cardAreaW - cardGapT * (nCols - 1)) / nCols;
        const cHT = H - bandH - H * 0.08;
        const cYT = bandH + H * 0.04;

        items.slice(0, 4).forEach((item, ti) => {
          const cx = cardAreaX + ti * (cWT + cardGapT);
          // 카드 본체 (Phase 8: 소프트 쉐도우 + 큰 라디우스)
          s.addShape('roundRect', { x: cx, y: cYT, w: cWT, h: cHT,
            fill: { color: 'FFFFFF' },
            line: { color: C.accentLight, width: 0.75 }, rectRadius: 0.14, shadow: PM_CARD_SHADOW });
          // 번호 배지
          const bdT = Math.min(cWT * 0.25, 0.52);
          s.addShape('ellipse', { x: cx + cWT * 0.10, y: cYT + cHT * 0.12,
            w: bdT, h: bdT,
            fill: { color: C.primary }, line: { type: 'none' } });
          s.addText(String(ti + 1).padStart(2, '0'), {
            x: cx + cWT * 0.10, y: cYT + cHT * 0.12,
            w: bdT, h: bdT,
            fontSize: Math.round(bdT * 22), bold: true,
            color: C.textOnPrimary, align: 'center', valign: 'middle', fontFace: F });
          // 항목 텍스트
          s.addText(item, {
            x: cx + cWT * 0.08, y: cYT + cHT * 0.42,
            w: cWT * 0.84, h: cHT * 0.50,
            fontSize: Math.max(11, Math.round(14 - items.length * 0.4)),
            color: C.textSecondary,
            wrap: true, align: 'left', valign: 'top',
            lineSpacingMultiple: 1.45, fontFace: F });
          // 하단 액센트 스트립
          s.addShape('rect', { x: cx, y: cYT + cHT - 0.055, w: cWT, h: 0.055,
            fill: { color: C.primary }, line: { type: 'none' } });
        });

        addFavicon();
        addPageNum();

      // ════════════════════════════════════════════════
      } else if (layout === 'split') {
        // ── PPTMON S22 스타일 — 텍스트(58%) + 이미지(42%) 균형 분할 ──
        const isFlipped = (splitIdx % 2 === 1);
        splitIdx++;

        const imgW   = W * 0.42;           // 이미지 패널 폭 (42%) — PDF canvas와 동일
        const txtW2  = W - imgW;           // 텍스트 패널 폭 (58%)
        const imgX   = isFlipped ? 0 : txtW2;
        const txtX2  = isFlipped ? imgW : 0;
        const pad    = W * 0.04;           // 내부 패딩 (W의 4%)
        const cX     = txtX2 + pad;
        const cW     = txtW2 - pad * 2;

        // body가 없을 때 텍스트 패널에 primary 색상으로 bold 변형 (꽉 찬 느낌)
        const splitBold = body.length === 0 && !sub;
        const txtPanelColor = splitBold ? C.primary : 'FFFFFF';
        const splitHlColor  = splitBold ? 'FFFFFF' : C.textPrimary;

        // 슬라이드 배경 + 텍스트 패널
        s.background = { color: splitBold ? C.primary : 'FFFFFF' };
        s.addShape('rect', { x: txtX2, y: 0, w: txtW2, h: H,
          fill: { color: txtPanelColor }, line: { type: 'none' } });

        // 이미지 패널 (다크 배경 + cover 크롭 — dark bar 없이 패널 채움)
        s.addShape('rect', { x: imgX, y: 0, w: imgW, h: H,
          fill: { color: bgDark }, line: { type: 'none' } });
        if (bgData) {
          s.addImage({ data: bgData, x: imgX, y: 0, w: imgW, h: H,
            sizing: { type: 'cover', w: imgW, h: H } });
          s.addShape('rect', { x: imgX, y: 0, w: imgW, h: H,
            fill: { color: '000000', transparency: 32 }, line: { type: 'none' } });
        } else {
          // 이미지 없을 때: 워터마크 + 글로우 장식
          // 중앙 대형 ellipse (밝은 흰색 계열 — 어두운 bgDark 위에 가시성 확보)
          s.addShape('ellipse', { x: imgX + imgW * 0.10, y: -H * 0.20,
            w: imgW * 1.20, h: H * 1.20,
            fill: { color: 'FFFFFF', transparency: 90 }, line: { type: 'none' } });
          // 우하단 보조 ellipse
          s.addShape('ellipse', { x: imgX + imgW * 0.50, y: H * 0.50,
            w: imgW * 0.70, h: imgW * 0.70,
            fill: { color: C.primary, transparency: 70 }, line: { type: 'none' } });
          // 회사명 워터마크 텍스트
          s.addText((companyName || '').toUpperCase(), {
            x: imgX + 0.10, y: H * 0.28, w: imgW - 0.10, h: H * 0.44,
            fontSize: 52, bold: true, color: 'FFFFFF', transparency: 82,
            align: 'center', valign: 'middle', fontFace: F, wrap: true });
        }

        // 패널 경계 수직 액센트 바
        const divX = isFlipped ? imgW - 0.02 : txtW2;
        s.addShape('rect', { x: divX, y: 0, w: 0.04, h: H,
          fill: { color: C.primary }, line: { type: 'none' } });

        // eyebrow pill (split) — 슬라이드 좌상단 고정 (레이아웃 flip 무관하게 일관성 유지)
        if (eyebrow) {
          const ewStr = eyebrow.toUpperCase();
          const ewLen = ewStr.replace(/[^\x00-\xff]/g, 'xx').length;
          const ewW = Math.min(ewLen * 0.125 + 0.48, 3.5), ewH = 0.28;
          // splitBold(어두운 배경)이면 흰 배경+어두운 텍스트, 밝은 배경이면 primary 색
          const ewFill = splitBold
            ? { color: 'FFFFFF' }
            : { color: C.primary };
          s.addShape('roundRect', { x: 0.28, y: 0.12, w: ewW, h: ewH,
            fill: ewFill, line: { type: 'none' }, rectRadius: ewH / 2 });
          s.addText(ewStr, { x: 0.28, y: 0.12, w: ewW, h: ewH,
            fontSize: 8.5, bold: true, color: splitBold ? '1A1A1A' : C.textOnPrimary, charSpacing: 2,
            align: 'center', valign: 'middle', fontFace: F, wrap: false });
        }

        // 헤드라인 — fontSize + 예상 줄수 기반 동적 높이
        const hlFsSplit = hl.length > 24 ? 22 : hl.length > 18 ? 26 : 30;
        const hlLineH = (hlFsSplit / 72) * 1.35;          // 한 줄 높이 (인치)
        const hlH = Math.min(hlLineH * 3.2, H * 0.26);   // 최대 3.2줄 또는 H*26%
        s.addText(hl, {
          x: cX, y: H * 0.13, w: cW, h: hlH,
          fontSize: hlFsSplit, bold: true, color: splitHlColor,
          wrap: true, shrinkText: true, align: 'left', valign: 'top',
          lineSpacingMultiple: 1.25, fontFace: FH });

        // PPTMON 포인트 언더라인 (헤드라인 바로 아래)
        const ulY = H * 0.13 + hlH + 0.06;
        s.addShape('rect', { x: cX, y: ulY, w: cW * 0.20, h: 0.05,
          fill: { color: splitBold ? 'FFFFFF' : C.primary }, line: { type: 'none' } });

        let contentY = ulY + 0.12;
        if (sub) {
          s.addText(sub, {
            x: cX, y: contentY, w: cW, h: H * 0.09,
            fontSize: 14, bold: true, color: C.primary,
            wrap: true, valign: 'top', lineSpacingMultiple: 1.3, fontFace: F });
          contentY += H * 0.10;
        }

        if (body.length > 0) {
          s.addText(body.slice(0, 5).map(b => '·  ' + b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '')).join('\n'), {
            x: cX, y: contentY, w: cW, h: H - contentY - H * 0.08,
            fontSize: 12.5, color: C.textSecondary,
            wrap: true, align: 'left', valign: 'top',
            lineSpacingMultiple: 1.9, fontFace: F });
        }

        // 플립된 split은 텍스트 패널이 우측 — copyright를 텍스트 패널 안으로 이동
        addCopyright(null, isFlipped ? imgW + 0.48 : 0.48);
        addFavicon();
        addPageNum();

      // ════════════════════════════════════════════════
      } else if (layout === 'cards') {
        // ── Cards 3종 변형: right(이미지 우) / left(이미지 좌) / center(이미지 없음) ──
        const imgPanW = W * 0.40;   // 이미지 패널 폭 (40% — 기존 30%에서 확대)
        const isLeft  = cardMode === 'left';
        const isCenter = cardMode === 'center';

        // 콘텐츠 영역 좌표
        const imgX  = isCenter ? -1 : (isLeft ? 0 : W - imgPanW);
        const cPad  = W * 0.036;
        const cAreaX = isCenter ? 0 : (isLeft ? imgPanW : 0);
        const cAreaW = isCenter ? W : (W - imgPanW);
        const cX    = cAreaX + cPad;
        const cW    = cAreaW - cPad * 2;

        // ── isCenter: 이미지 없는 순수 콘텐츠 → Adaptive Cards 레이아웃으로 전환 ──
        cards_block: {
        if (isCenter) {
          pm_addAdaptiveCards(s, C, fonts, hl, body.length > 0 ? body : (sub ? [sub] : [hl]), eyebrow);
          addPageNum(C.textMuted);
          addFavicon();
          break cards_block;
        }

        // 배경 — 이미지 없는 center 모드는 다크 배경으로 시각적 채움
        s.background = { color: C.bg };

        // 이미지 패널 (center 아닐 때)
        if (!isCenter) {
          s.addShape('rect', { x: imgX, y: 0, w: imgPanW, h: H,
            fill: { color: bgDark }, line: { type: 'none' } });
          if (bgData) {
            s.addImage({ data: bgData, x: imgX, y: 0, w: imgPanW, h: H,
              sizing: { type: 'cover', w: imgPanW, h: H } });
            s.addShape('rect', { x: imgX, y: 0, w: imgPanW, h: H,
              fill: { color: '000000', transparency: 40 }, line: { type: 'none' } });
          }
          // 패널 경계 수직 액센트 바
          const divX = isLeft ? imgPanW - W * 0.003 : W - imgPanW - W * 0.0025;
          s.addShape('rect', { x: divX, y: 0, w: W * 0.005, h: H,
            fill: { color: C.primary }, line: { type: 'none' } });
        }

        // 상단/하단 액센트 라인
        addAccentLines();
        // 좌측 수직 액센트 바 (center 이미지없는 슬라이드에만)
        if (isCenter) {
          s.addShape('rect', { x: 0, y: 0, w: W * 0.008, h: H,
            fill: { color: C.primary }, line: { type: 'none' } });
        }

        // ── 헤더 eyebrow pill (cards — 슬라이드 좌상단 고정) ──
        if (eyebrow) {
          const ewStr = eyebrow.toUpperCase();
          const ewLen = ewStr.replace(/[^\x00-\xff]/g, 'xx').length;
          const ewW = Math.min(ewLen * 0.125 + 0.48, 3.5), ewH = 0.28;
          s.addShape('roundRect', { x: 0.28, y: 0.12, w: ewW, h: ewH,
            fill: { color: C.primary }, line: { type: 'none' }, rectRadius: ewH / 2 });
          s.addText(ewStr, { x: 0.28, y: 0.12, w: ewW, h: ewH,
            fontSize: 8.5, bold: true, color: C.textOnPrimary, charSpacing: 2,
            align: 'center', valign: 'middle', fontFace: F, wrap: false });
        }
        const _bodyCount = (body || []).length;
        const hlFsCards = hl.length > 24 ? 20 : hl.length > 18 ? 24 : (_bodyCount >= 4 ? 26 : 30);
        s.addText(hl, {
          x: cX, y: H * 0.14, w: cW, h: H * 0.20,
          fontSize: hlFsCards, bold: true, color: isCenter ? 'FFFFFF' : C.textPrimary,
          wrap: true, shrinkText: true, align: 'left', valign: 'top',
          lineSpacingMultiple: 1.25, fontFace: FH });
        s.addShape('rect', { x: cX, y: H * 0.36, w: cW * 0.18, h: 0.05,
          fill: { color: C.primary }, line: { type: 'none' } });
        if (sub) {
          s.addText(sub, {
            x: cX, y: H * 0.38, w: cW, h: H * 0.07,
            fontSize: 15, color: C.primary,
            wrap: true, valign: 'top', lineSpacingMultiple: 1.3, fontFace: F });
        }
        // isCenter: 우측에 대형 장식 원 (컬러로 공간 채움)
        if (isCenter) {
          s.addShape('ellipse', { x: W * 0.75, y: -H * 0.12, w: H * 0.85, h: H * 0.85,
            fill: { color: C.primary, transparency: 88 }, line: { type: 'none' } });
        }

        // ── 카드 그리드 ──────────────────────────────────
        const items   = body.length > 0 ? body : (sub ? [sub] : [hl]);
        const is2x2   = items.length >= 4;   // 4개 → 2×2 그리드
        const numCols = is2x2 ? 2 : Math.min(Math.max(items.length, 2), 3);
        const numRows = is2x2 ? 2 : 1;
        const cardGap = W * 0.016;
        const cardY   = is2x2 ? (sub ? H * 0.42 : H * 0.36) : (sub ? H * 0.48 : H * 0.43);
        const cardH   = (H - cardY - (is2x2 ? H * 0.20 : H * 0.08) - cardGap * (numRows - 1)) / numRows;
        const cardW   = (cW - cardGap * (numCols - 1)) / numCols;
        const circD   = Math.min(cardW * 0.22, 0.60);
        const circR   = circD / 2;

        const totalItems = items.slice(0, numCols * numRows).length;
        // 슬라이드 내 아이콘 일관성: 하나라도 아이콘이 있으면 모든 카드 아이콘 모드 사용
        const _anyHasIcon = items.slice(0, numCols * numRows).some(it => parseIconItem(it).icon);
        items.slice(0, numCols * numRows).forEach((item, ci) => {
          const col = ci % numCols, row = Math.floor(ci / numCols);
          const cx  = cX + col * (cardW + cardGap);
          const cy  = cardY + row * (cardH + cardGap);
          const cirX = cx + cardW / 2 - circR;
          // [아이콘 파싱] "[compass] 텍스트" 형식에서 아이콘 추출
          const parsed = parseIconItem(item);
          // 하나라도 아이콘이 있으면 모든 카드 아이콘 표시 (없는 카드는 'target' fallback)
          const resolvedIcon = _anyHasIcon ? (parsed.icon || 'target') : null;
          const hasIcon = !!resolvedIcon;
          const displayText = parsed.text;
          // 카드 색상 — 1-row(N≤3): 항상 컬러 배경 (꽉 찬 느낌), 2x2: 흰 배경
          const colorPalette = [C.accentDark, C.primary, _pm_bright(C.primary, -0.20)];
          const useColorCard = !is2x2;
          const cardFill = useColorCard ? colorPalette[ci % colorPalette.length] : 'FFFFFF';
          const cardTextColor = useColorCard ? 'FFFFFF' : C.textSecondary;
          // topOff: 모든 카드에서 내부 배지 공간만큼 (circle/icon이 카드 내부에 배치)
          const topOff = 0.10;
          // 카드 본체
          s.addShape('roundRect', {
            x: cx, y: cy + topOff, w: cardW, h: cardH - topOff,
            fill: { color: cardFill },
            line: useColorCard ? { type: 'none' } : { color: C.lineColor, width: 0.75 },
            rectRadius: 0.16, shadow: PM_CARD_SHADOW });
          // 2x2 카드: 상단 primary accent bar (레퍼런스 PDF 스타일)
          if (is2x2) {
            s.addShape('roundRect', { x: cx, y: cy + topOff, w: cardW, h: 0.08,
              fill: { color: C.primary }, line: { type: 'none' }, rectRadius: 0.06 });
          }
          // [1-row] 연결 삼각형 — 카드 상단 중간 높이
          if (!is2x2 && row === 0 && col < numCols - 1) {
            s.addShape('triangle', {
              x: cx + cardW + cardGap / 2 - 0.13, y: cy + topOff + cardH * 0.3,
              w: 0.26, h: 0.38,
              fill: { color: useColorCard ? 'FFFFFF' : C.accentLight },
              line: { type: 'none' }, rotate: 90 });
          }
          // 번호 배지 / 아이콘 — 텍스트 정렬(cx+cardW*0.07)에 맞춰 좌측 정렬
          const bd = is2x2 ? Math.min(cardW * 0.20, 0.56) : Math.min(cardW * 0.28, 0.80);
          const bdX = cx + cardW * 0.08;
          const bdY = cy + topOff + (is2x2 ? 0.14 : 0.20);
          const bdCircleColor = useColorCard ? 'FFFFFF' : C.primary;
          const bdTextColor   = useColorCard ? colorPalette[ci % colorPalette.length] : 'FFFFFF';
          if (hasIcon) {
            pm_addIcon(s, resolvedIcon, bdX, bdY, bd,
              useColorCard ? 'FFFFFF' : C.primary);
          } else {
            s.addShape('ellipse', { x: bdX, y: bdY, w: bd, h: bd,
              fill: { color: bdCircleColor }, line: { type: 'none' } });
            s.addText(`${ci + 1}`, { x: bdX, y: bdY, w: bd, h: bd,
              fontSize: Math.round(bd * 26), bold: true, color: bdTextColor,
              align: 'center', valign: 'middle', fontFace: F });
          }
          // 카드 텍스트 — 배지 아래 full-width (2x2/1-row 통일)
          const txtY = bdY + bd + (is2x2 ? 0.12 : 0.18);
          const txtX2 = cx + cardW * 0.07;
          const txtW2 = cardW * 0.86;
          const txtH = cy + topOff + cardH - topOff - txtY;
          // heading 파싱: "제목: 설명" 또는 "요약 → 설명" 형식 분리
          const _cdp = (() => {
            const s1 = displayText.indexOf(': ');
            if (s1 > 0 && s1 <= 22) return { h: displayText.slice(0, s1), b: displayText.slice(s1 + 2) };
            const s2 = displayText.indexOf(' → ');
            if (s2 > 0 && s2 <= 30) return { h: displayText.slice(0, s2), b: displayText.slice(s2 + 3) };
            return { h: '', b: displayText };
          })();
          // [icon-name] prefix가 헤딩에 남은 경우 제거 (parseIconItem 미적용 케이스 방어)
          if (_cdp.h) _cdp.h = _cdp.h.replace(/^\[[^\]]+\]\s*/, '');
          if (_cdp.b) _cdp.b = _cdp.b.replace(/^\[[^\]]+\]\s*/, '');
          if (_cdp.h) {
            const hH = 0.28;
            s.addText(_cdp.h, { x: txtX2, y: txtY, w: txtW2, h: hH,
              fontFace: F, fontSize: 14, bold: true,
              color: useColorCard ? 'FFFFFF' : '111111',
              wrap: true, valign: 'top', lineSpacingMultiple: 1.2 });
            s.addShape('rect', { x: txtX2, y: txtY + hH, w: txtW2 * 0.50, h: 0.012,
              fill: { color: useColorCard ? 'FFFFFF' : C.lineColor,
                      transparency: useColorCard ? 55 : 0 }, line: { type: 'none' } });
            const descY = txtY + hH + 0.04;
            s.addText(_cdp.b, { x: txtX2, y: descY, w: txtW2,
              h: Math.max(cy + cardH + topOff - descY - 0.16, 0.3),
              fontFace: F, fontSize: 12, color: cardTextColor,
              wrap: true, align: 'left', valign: 'top', lineSpacingMultiple: 1.35 });
          } else {
            s.addText(displayText, {
              x: txtX2, y: txtY, w: txtW2, h: Math.max(txtH, 0.3),
              fontSize: is2x2 ? 13 : 14, color: cardTextColor,
              wrap: true, align: 'left', valign: 'top',
              lineSpacingMultiple: 1.4, fontFace: F });
          }
        });

        addCopyright();
        addFavicon();
        addPageNum();
        } // end cards_block

      // ════════════════════════════════════════════════
      } else if (layout === 'portfolio') {
        // ── Portfolio: Typography-first dual-color split (C.primary + C2, narrative-type별) ──
        const NT = narrativeType;
        const panRight = portMode === 'right';  // left/right 교차

        if (NT === 'C') {
          if (bgData) {
            // ── C-type IMAGE-FIRST: 풀 블리드 이미지 + 오버레이 + 하단 텍스트 박스 ──
            addFullBg();
            // 하단 그라디언트 오버레이 (텍스트 가독성)
            s.addShape('rect', { x: 0, y: H * 0.48, w: W, h: H * 0.52,
              fill: { color: '000000', transparency: 25 }, line: { type: 'none' } });
            // eyebrow badge (흰 배경 + 어두운 텍스트 — 어두운 showcase 배경에서 선명하게)
            if (eyebrow) { const ewStr3 = eyebrow.toUpperCase();
              const ewW3 = Math.min(ewStr3.length * 0.092 + 0.40, 5.0), ewH3 = 0.27;
              const ewX3 = W * 0.06;
              s.addShape('roundRect', { x: ewX3, y: H * 0.52, w: ewW3, h: ewH3,
                fill: { color: 'FFFFFF' }, line: { type: 'none' }, rectRadius: ewH3 / 2 });
              s.addText(ewStr3, { x: ewX3, y: H * 0.52, w: ewW3, h: ewH3,
                fontSize: 9, bold: true, color: '1A1A1A', charSpacing: 2,
                align: 'center', valign: 'middle', fontFace: F, wrap: false }); }
            // 헤드라인
            s.addText(hl, { x: W * 0.06, y: H * 0.58, w: W * 0.88, h: H * 0.22,
              fontSize: 32, bold: true, color: 'FFFFFF',
              wrap: true, shrinkText: true, align: 'left', valign: 'top', lineSpacingMultiple: 1.2, fontFace: FH });
            // 구분선
            s.addShape('rect', { x: W * 0.06, y: H * 0.80, w: W * 0.12, h: 0.025,
              fill: { color: 'FFFFFF', transparency: 40 }, line: { type: 'none' } });
            // sub + body
            let pfYc = H * 0.83;
            if (sub) { s.addText(sub, { x: W * 0.06, y: pfYc, w: W * 0.88, h: H * 0.08,
              fontSize: 13, color: 'EEEEEE', wrap: true, align: 'left', valign: 'top', fontFace: F });
              pfYc += H * 0.07; }
            body.slice(0, 3).forEach(b => {
              if (pfYc + H * 0.05 > H * 0.95) return;
              s.addText('·  ' + b.replace(/^\[[\w-\s]+\]\s*/i, ''), { x: W * 0.06, y: pfYc, w: W * 0.85, h: H * 0.05,
                fontSize: 11, color: 'CCCCCC', wrap: true, align: 'left', valign: 'top', fontFace: F });
              pfYc += H * 0.05; });
            addCopyright('AAAAAA');
            addFavicon();
            addPageNum('AAAAAA');
          } else {
            // ── C-type TEXT-FIRST: 이미지 없을 때 2색 패널 ──
            const litW = W * 0.55, darkW = W - litW;
            const litX = panRight ? darkW : 0;
            const drkX = panRight ? 0 : litW;
            s.background = { color: 'F4F4F8' };
            s.addShape('rect', { x: drkX, y: 0, w: darkW, h: H,
              fill: { color: C.primary }, line: { type: 'none' } });
            const bdX2 = panRight ? darkW - 0.022 : litW;
            s.addShape('rect', { x: bdX2, y: 0, w: 0.022, h: H,
              fill: { color: C.accentLight }, line: { type: 'none' } });
            if (companyName) s.addText(companyName.toUpperCase(), {
              x: litX, y: H * 0.02, w: litW, h: H * 0.22,
              fontSize: 42, bold: true, color: C.primary, transparency: 88,
              align: panRight ? 'right' : 'left', valign: 'middle', fontFace: F, wrap: false });
            if (eyebrow) { const ewStr2 = eyebrow.toUpperCase();
              const ewW2 = Math.min(ewStr2.length * 0.092 + 0.40, 5.0), ewH2 = 0.28;
              const ewX2 = panRight ? litX + litW - ewW2 - litW * 0.06 : litX + litW * 0.07;
              s.addShape('roundRect', { x: ewX2, y: H * 0.14, w: ewW2, h: ewH2,
                fill: { color: C.primary }, line: { type: 'none' }, rectRadius: ewH2 / 2 });
              s.addText(ewStr2, { x: ewX2, y: H * 0.14, w: ewW2, h: ewH2,
                fontSize: 9, bold: true, color: C.textOnPrimary, charSpacing: 2,
                align: 'center', valign: 'middle', fontFace: F, wrap: false }); }
            const litTxtX2 = panRight ? litX + litW * 0.06 : litX + litW * 0.07;
            const litTxtW2 = litW * 0.87;
            s.addText(hl, { x: litTxtX2, y: H * 0.24, w: litTxtW2, h: H * 0.33,
              fontSize: 30, bold: true, color: '111111',
              wrap: true, shrinkText: true, align: 'left', valign: 'top', lineSpacingMultiple: 1.25, fontFace: FH });
            s.addShape('rect', { x: litTxtX2, y: H * 0.59, w: litTxtW2 * 0.30, h: 0.025,
              fill: { color: C.primary }, line: { type: 'none' } });
            let pfY3 = H * 0.63;
            if (sub) { s.addText(sub, { x: litTxtX2, y: pfY3, w: litTxtW2, h: H * 0.10,
              fontSize: 14, color: '444444', wrap: true, align: 'left', valign: 'top', fontFace: F });
              pfY3 += H * 0.11; }
            body.slice(0, 2).forEach(b => {
              if (pfY3 + H * 0.08 > H * 0.88) return;
              s.addText('·  ' + b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, ''), { x: litTxtX2, y: pfY3, w: litTxtW2, h: H * 0.08,
                fontSize: 12, color: '666666', wrap: true, align: 'left', valign: 'top', fontFace: F });
              pfY3 += H * 0.09; });
            const drkTxtX = drkX + darkW * 0.10;
            if (companyName) s.addText(companyName.toUpperCase(), {
              x: drkTxtX, y: H * 0.38, w: darkW * 0.80, h: H * 0.24,
              fontSize: 24, bold: true, color: 'FFFFFF', charSpacing: 2,
              wrap: true, align: 'left', valign: 'middle', lineSpacingMultiple: 1.3, fontFace: F });
            addCopyright('888888');
            addFavicon();
            addPageNum('888888');
          }

        } else {
          // A (default) / B / D / F: config-based 통합 렌더
          const _pf = ({
            B: { bg: '08080E', circTr: 90, hlBold: true,  subClr: C.accentLight, bodyClr: 'AAAAAA', footClr: '888888',
                 logoFbClr: 'FFFFFF', logoFbBold: true,  logoFbSp: 3 },
            D: { bg: '07070D', circTr: 96, hlBold: false, subClr: '888888',      bodyClr: '666666', footClr: '444444',
                 logoFbClr: C.accentLight, logoFbBold: false, logoFbSp: 4 }
          })[NT] || { bg: '090912', circTr: 90, hlBold: true, subClr: C.accentLight, bodyClr: 'AAAAAA', footClr: '888888',
                      logoFbClr: 'FFFFFF', logoFbBold: true, logoFbSp: 3 };
          const panW = W * 0.38;
          const panX = panRight ? W - panW : 0;
          const cntX = panRight ? 0 : panW;
          const cntW = W - panW;
          s.background = { color: _pf.bg };
          if (NT === 'D') {
            // Luxury: 극세선 테두리 (패널 없음)
            s.addShape('rect', { x: 0, y: 0, w: 0.04, h: H, fill: { color: C.primary }, line: { type: 'none' } });
            s.addShape('rect', { x: W - 0.04, y: 0, w: 0.04, h: H, fill: { color: C.primary }, line: { type: 'none' } });
            s.addShape('rect', { x: 0, y: 0, w: W, h: 0.03, fill: { color: C.primary }, line: { type: 'none' } });
            s.addShape('rect', { x: 0, y: H - 0.03, w: W, h: 0.03, fill: { color: C.primary }, line: { type: 'none' } });
          } else {
            // A / B / F: solid primary panel
            s.addShape('rect', { x: panX, y: 0, w: panW, h: H, fill: { color: C.primary }, line: { type: 'none' } });
            const divX = panRight ? W - panW - 0.02 : panW;
            s.addShape('rect', { x: divX, y: 0, w: 0.022, h: H, fill: { color: C.accentLight }, line: { type: 'none' } });
            s.addShape('rect', { x: panX + panW * 0.09, y: H * 0.22, w: panW * 0.82, h: 0.03, fill: { color: 'FFFFFF', transparency: 70 }, line: { type: 'none' } });
            s.addShape('rect', { x: panX + panW * 0.09, y: H * 0.75, w: panW * 0.82, h: 0.018, fill: { color: C.accentLight }, line: { type: 'none' } });
          }
          // 대형 C2 데코 원
          const circSz = H * 1.10;
          const circX = panRight ? cntX - circSz * 0.35 : cntX + cntW - circSz * 0.65;
          s.addShape('ellipse', { x: circX, y: -H * 0.15, w: circSz, h: circSz,
            fill: { color: C.accentLight, transparency: _pf.circTr }, line: { type: 'none' } });
          // 로고
          addLogo(panX + panW * 0.08, H * 0.08, 1.6, 0.46);
          if (!showLogo && companyName) s.addText(companyName.toUpperCase(), {
            x: panX + panW * 0.05, y: H * 0.09, w: panW * 0.90, h: 0.40,
            fontSize: 10, bold: _pf.logoFbBold, color: _pf.logoFbClr, charSpacing: _pf.logoFbSp,
            align: 'center', valign: 'middle', fontFace: F });
          // 콘텐츠 영역
          const cntTxtX = cntX + (panRight ? cntW * 0.06 : cntW * 0.07);
          const cntTxtW = cntW * 0.87;
          if (eyebrow) {
            const ewStr = eyebrow.toUpperCase();
            const ewW = Math.min(ewStr.length * 0.092 + 0.40, 5.0), ewH = 0.28;
            s.addShape('roundRect', { x: cntTxtX, y: H * 0.12, w: ewW, h: ewH,
              fill: { color: C.primary }, line: { type: 'none' }, rectRadius: ewH / 2 });
            s.addText(ewStr, { x: cntTxtX, y: H * 0.12, w: ewW, h: ewH,
              fontSize: 9, bold: true, color: 'FFFFFF', charSpacing: 2,
              align: 'center', valign: 'middle', fontFace: F, wrap: false }); }
          s.addText(hl, { x: cntTxtX, y: H * 0.24, w: cntTxtW, h: H * 0.35,
            fontSize: 30, bold: _pf.hlBold, color: 'FFFFFF',
            wrap: true, shrinkText: true, align: 'left', valign: 'top', lineSpacingMultiple: 1.25, fontFace: FH });
          s.addShape('rect', { x: cntTxtX, y: H * 0.61, w: cntTxtW * 0.35, h: 0.022,
            fill: { color: C.accentLight }, line: { type: 'none' } });
          let _pfY = H * 0.65;
          if (sub) { s.addText(sub, { x: cntTxtX, y: _pfY, w: cntTxtW, h: H * 0.11,
            fontSize: 14, bold: true, color: _pf.subClr, wrap: true, align: 'left', valign: 'top', fontFace: F });
            _pfY += H * 0.12; }
          body.slice(0, 3).forEach(b => {
            if (_pfY + H * 0.09 > H * 0.92) return;
            s.addText('·  ' + b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, ''), { x: cntTxtX, y: _pfY, w: cntTxtW, h: H * 0.09,
              fontSize: 13, color: _pf.bodyClr, wrap: true, align: 'left', valign: 'top', lineSpacingMultiple: 1.3, fontFace: F });
            _pfY += H * 0.10; });
          addCopyright(_pf.footClr);
          addFavicon();
          addPageNum(_pf.footClr);
        }

      // ════════════════════════════════════════════════
      } else if (layout === 'section') {
        // ── Section Divider: 좌측 40% 다크 패널(번호+제목) + 우측 60% 풀 포토 ──
        const secPanW = W * 0.40;

        // 전체 배경 (다크)
        s.background = { color: bgDark };

        // 우측 포토 패널
        if (bgData) {
          s.addImage({ data: bgData, x: secPanW, y: 0, w: W - secPanW, h: H,
            sizing: { type: 'cover', w: W - secPanW, h: H } });
          s.addShape('rect', { x: secPanW, y: 0, w: W - secPanW, h: H,
            fill: { color: '000000', transparency: 30 }, line: { type: 'none' } });
        } else {
          s.addShape('rect', { x: secPanW, y: 0, w: W - secPanW, h: H,
            fill: { color: _pm_bright(bgDark, 0.12) }, line: { type: 'none' } });
          // 크로스 그리드 패턴 (이미지 없을 때 우측 패널 장식)
          const gridStep = 0.72;
          const gridColor = C.primary;
          for (let gx = secPanW + gridStep * 0.5; gx < W; gx += gridStep) {
            s.addShape('rect', { x: gx - 0.006, y: 0, w: 0.012, h: H,
              fill: { color: gridColor, transparency: 82 }, line: { type: 'none' } });
          }
          for (let gy = gridStep * 0.5; gy < H; gy += gridStep) {
            s.addShape('rect', { x: secPanW, y: gy - 0.006, w: W - secPanW, h: 0.012,
              fill: { color: gridColor, transparency: 82 }, line: { type: 'none' } });
          }
        }

        // 좌측 다크 패널 (bgDark 위에 약간 더 진하게)
        s.addShape('rect', { x: 0, y: 0, w: secPanW, h: H,
          fill: { color: bgDark }, line: { type: 'none' } });

        // 수직 액센트 구분선
        s.addShape('rect', { x: secPanW - 0.025, y: 0, w: 0.05, h: H,
          fill: { color: C.primary }, line: { type: 'none' } });

        // 상단 액센트 바 (좌측 패널만)
        s.addShape('rect', { x: 0, y: 0, w: secPanW, h: 0.07,
          fill: { color: C.primary }, line: { type: 'none' } });

        // 섹션 번호 (대형, 반투명)
        const secNumStr = String(pptxSectionCounter).padStart(2, '0');
        s.addText(secNumStr, {
          x: W * 0.04, y: H * 0.08, w: secPanW * 0.85, h: H * 0.30,
          fontSize: 80, bold: true, color: C.primary,
          transparency: 20, align: 'left', valign: 'top', fontFace: F });

        // 섹션 번호 아래 액센트 라인
        s.addShape('rect', { x: W * 0.04, y: H * 0.43, w: secPanW * 0.22, h: 0.04,
          fill: { color: C.primary }, line: { type: 'none' } });

        // 메인 타이틀
        s.addText(hl, {
          x: W * 0.04, y: H * 0.47, w: secPanW - W * 0.06, h: H * 0.36,
          fontSize: 26, bold: true, color: 'FFFFFF',
          wrap: true, shrinkText: true, align: 'left', valign: 'top',
          lineSpacingMultiple: 1.25, fontFace: FH });

        // 서브 또는 body pill 태그 (하단)
        if (sub) {
          s.addText(sub, {
            x: W * 0.04, y: H * 0.83, w: secPanW - W * 0.06, h: H * 0.11,
            fontSize: 13, color: 'AAAAAA',
            wrap: true, align: 'left', valign: 'top', fontFace: F });
        } else if (body.length > 0) {
          let pillX = W * 0.04;
          let pillRowY = H * 0.83;
          const pillH = 0.27;
          body.slice(0, 5).forEach(tag => {
            const tagTrim = tag.slice(0, 20);
            const tw = Math.min(tagTrim.length * 0.105 + 0.28, secPanW - W * 0.10);
            if (pillX + tw > secPanW - W * 0.04) { pillX = W * 0.04; pillRowY += pillH + 0.09; }
            s.addShape('roundRect', { x: pillX, y: pillRowY, w: tw, h: pillH,
              fill: { color: C.primary, transparency: 55 }, line: { type: 'none' }, rectRadius: pillH / 2 });
            s.addText(tagTrim, { x: pillX, y: pillRowY, w: tw, h: pillH,
              fontFace: F, fontSize: 8, color: 'FFFFFF',
              align: 'center', valign: 'middle' });
            pillX += tw + 0.10;
          });
        }

        addPageNum('888888');

      // ════════════════════════════════════════════════
      } else if (layout === 'comparison') {
        // ── Comparison: AS-IS (neutral_dark) vs TO-BE (brand) 2컬럼 ──
        s.background = { color: C.bg };
        addAccentLines();

        // 헤더 (split/cards와 y 통일)
        s.addText(eyebrow, {
          x: W * 0.04, y: H * 0.08, w: W * 0.92, h: H * 0.05,
          fontSize: 11, bold: true, color: C.eyebrowFill || C.primary,
          charSpacing: 3, valign: 'top', fontFace: F });
        s.addText(hl, {
          x: W * 0.04, y: H * 0.13, w: W * 0.92, h: H * 0.17,
          fontSize: 26, bold: true, color: C.textPrimary,
          wrap: true, align: 'left', valign: 'top',
          lineSpacingMultiple: 1.2, fontFace: FH });
        // 헤드라인 아래 포인트 선
        s.addShape('rect', { x: W * 0.04, y: H * 0.32, w: W * 0.10, h: 0.04,
          fill: { color: C.primary }, line: { type: 'none' } });

        // 컬럼 레이아웃
        const cmpColY  = H * 0.36;
        const cmpColH  = H - cmpColY - H * 0.07;
        const cmpGap   = W * 0.02;
        const cmpColL  = W * 0.04;
        const cmpHdrH  = H * 0.09;

        // body 5개 이상: AS-IS + TO-BE 2컬럼 / 미만: TO-BE 단독 전체 너비
        const showTwoCol  = body.length >= 5;
        const cmpColW     = showTwoCol ? (W - W * 0.08 - cmpGap) / 2 : W - W * 0.08;
        const cmpColR     = cmpColL + cmpColW + cmpGap;
        const halfN       = showTwoCol ? Math.ceil(body.length / 2) : 0;
        const beforeItems = body.slice(0, halfN);
        const afterItems  = body.slice(halfN).length > 0 ? body.slice(halfN) : body.slice(0, 5);

        // ── VS 배지 (두 컬럼 중앙, showTwoCol일 때) ──
        if (showTwoCol) {
          const vsD = 0.56;
          const vsX = cmpColL + cmpColW + cmpGap / 2 - vsD / 2;
          const vsY = cmpColY + cmpColH / 2 - vsD / 2;
          s.addShape('ellipse', { x: vsX, y: vsY, w: vsD, h: vsD,
            fill: { color: C.primary }, line: { color: 'FFFFFF', width: 2 } });
          s.addText('VS', { x: vsX, y: vsY, w: vsD, h: vsD,
            fontFace: F, fontSize: 13, bold: true, color: C.textOnPrimary,
            align: 'center', valign: 'middle' });
        }

        if (showTwoCol) {
          // ── AS-IS 컬럼 (neutral_dark 헤더) ──
          s.addShape('roundRect', { x: cmpColL, y: cmpColY, w: cmpColW, h: cmpHdrH,
            fill: { color: '4D4D4D' }, line: { type: 'none' }, rectRadius: 0.14 });
          s.addText('AS-IS  현재 상황', {
            x: cmpColL, y: cmpColY, w: cmpColW, h: cmpHdrH,
            fontSize: 14, bold: true, color: 'FFFFFF',
            align: 'center', valign: 'middle', fontFace: F });
          s.addShape('roundRect', { x: cmpColL, y: cmpColY + cmpHdrH + 0.05,
            w: cmpColW, h: cmpColH - cmpHdrH - 0.05,
            fill: { color: 'F5F5F5' }, line: { color: 'DDDDDD', width: 1 }, rectRadius: 0.14, shadow: PM_CARD_SHADOW });
          s.addText(beforeItems.slice(0, 4).map(b => '✕  ' + b).join('\n'), {
            x: cmpColL + cmpColW * 0.07, y: cmpColY + cmpHdrH + 0.18,
            w: cmpColW * 0.86, h: cmpColH - cmpHdrH - 0.28,
            fontSize: 13, color: '555555',
            wrap: true, align: 'left', valign: 'top',
            lineSpacingMultiple: 1.6, fontFace: F });
        }

        // ── TO-BE 컬럼 (brand color 헤더 — 2컬럼일 때만) ──
        const tobeX = showTwoCol ? cmpColR : cmpColL;
        if (showTwoCol) {
          s.addShape('roundRect', { x: tobeX, y: cmpColY, w: cmpColW, h: cmpHdrH,
            fill: { color: C.primary }, line: { type: 'none' }, rectRadius: 0.14 });
          s.addText('TO-BE  개선 방향', {
            x: tobeX, y: cmpColY, w: cmpColW, h: cmpHdrH,
            fontSize: 14, bold: true, color: C.textOnPrimary,
            align: 'center', valign: 'middle', fontFace: F });
          s.addShape('roundRect', { x: tobeX, y: cmpColY + cmpHdrH + 0.05,
            w: cmpColW, h: cmpColH - cmpHdrH - 0.05,
            fill: { color: 'FFFFFF' }, line: { color: C.primary, transparency: 65, width: 1.5 }, rectRadius: 0.14, shadow: PM_CARD_SHADOW });
          s.addText(afterItems.slice(0, 5).map(b => '·  ' + b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '')).join('\n'), {
            x: tobeX + cmpColW * 0.05, y: cmpColY + cmpHdrH + 0.18,
            w: cmpColW * 0.90, h: cmpColH - cmpHdrH - 0.28,
            fontSize: 13, color: C.textSecondary,
            wrap: true, align: 'left', valign: 'top',
            lineSpacingMultiple: 1.6, fontFace: F });
        } else {
          // 단독 컬럼: 헤더 박스 없이 바로 bullet list
          s.addText(afterItems.slice(0, 6).map(b => '·  ' + b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '')).join('\n'), {
            x: cmpColL, y: cmpColY, w: cmpColW, h: cmpColH,
            fontSize: 16, color: C.textSecondary,
            wrap: true, align: 'left', valign: 'top',
            lineSpacingMultiple: 1.9, fontFace: F });
        }

        if (showTwoCol) {
          // 중앙 화살표
          s.addShape('triangle', {
            x: cmpColL + cmpColW + cmpGap / 2 - 0.14,
            y: cmpColY + cmpColH / 2 - 0.14,
            w: 0.28, h: 0.28,
            fill: { color: C.primary }, line: { type: 'none' }, rotate: 90 });
        }

        addCopyright();
        addFavicon();
        addPageNum();

      // ════════════════════════════════════════════════
      } else if (layout === 'timeline') {
        // ── PPTMON S26 지그재그 타임라인 ─────────────────
        const _pmParse = b => {
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
          const sp = b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, b.length);
          return { heading: b.slice(0, cut).trim(), body: b.slice(cut).trim() };
        };
        const tlItems = body.length > 0
          ? body.slice(0, 5).map((b, i) => {
              const p = _pmParse(b);
              return { year: String(i + 1), heading: p.heading, body: p.body };
            })
          : [{ year: '1', heading: hl, body: sub }];
        pm_addZigzagTimeline(s, C, fonts, hl, tlItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === '4step') {
        // ── PPTMON S28 4-스텝 프로세스 ────────────────────
        const _pmParse = b => {
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
          const sp = b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, b.length);
          return { heading: b.slice(0, cut).trim(), body: b.slice(cut).trim() };
        };
        const stepsData = body.length > 0
          ? body.slice(0, 4).map((b, i) => {
              const p = _pmParse(b);
              return { number: String(i + 1).padStart(2, '0'),
                       label: `Step ${i + 1}`,
                       heading: p.heading, body: p.body };
            })
          : [{ number: '01', label: 'Step 1', heading: hl, body: sub }];
        pm_add4StepProcess(s, C, fonts, hl, stepsData, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'radial') {
        // ── PPTMON S29 방사형 다이어그램 ──────────────────
        const _pmParse = b => {
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
          const sp = b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, b.length);
          return { heading: b.slice(0, cut).trim(), body: b.slice(cut).trim() };
        };
        const radCards = body.length > 0
          ? body.slice(0, 4).map(b => _pmParse(b))
          : [{ heading: hl, body: sub }];
        pm_addRadialDiagram(s, C, fonts, hl, sub || companyName, radCards, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'timeline_h') {
        // ── 수평 화살표 타임라인 (10p) ────────────────────
        const _pmParse = b => {
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
          const sp = b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, b.length);
          return { heading: b.slice(0, cut).trim(), body: b.slice(cut).trim() };
        };
        // infographic.data.events (company_history 타입) 우선 사용
        const tlhRaw = slide.infographic?.data?.events;
        const tlhItems = tlhRaw?.length > 0
          ? tlhRaw.slice(0, 6).map(e => ({
              label: String(e.year || ''),
              heading: e.label || '',
              body: e.desc || ''
            }))
          : body.length > 0
            ? body.slice(0, 6).map((b, i) => {
                const p = _pmParse(b);
                const isShort = p.heading.length <= 12;
                return { label: isShort ? p.heading : String(i + 1),
                         heading: isShort ? (p.body || p.heading) : p.heading,
                         body: isShort ? '' : p.body };
              })
            : [{ label: '1', heading: hl, body: sub }];
        pm_addHorizontalArrowTimeline(s, C, fonts, hl, tlhItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'circle4') {
        // ── 4개 원 묶음 다이어그램 (8p) ─────────────────
        const _pmParse = b => {
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
          const sp = b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, b.length);
          return { heading: b.slice(0, cut).trim(), body: b.slice(cut).trim() };
        };
        const c4Items = body.length > 0
          ? body.slice(0, 4).map(b => _pmParse(b))
          : [{ heading: hl, body: sub }];
        pm_addCircleDiagram4(s, C, fonts, hl, c4Items, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'converge4') {
        // ── 4개 수렴 다이어그램 (13p) ─────────────────────
        const _pmParse = b => {
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
          const sp = b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, b.length);
          return { heading: b.slice(0, cut).trim(), body: b.slice(cut).trim() };
        };
        const cv4Items = body.length > 0
          ? body.slice(0, 4).map(b => _pmParse(b))
          : [{ heading: hl, body: sub }];
        pm_addConvergeDiagram4(s, C, fonts, hl, cv4Items, sub || companyName, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'swot4') {
        // ── SWOT 2×2 그리드 (NEW-F) ──────────────────────
        const sw4Items = body.slice(0, 4).map(b => {
          const ci = b.indexOf(':');
          return ci > 0 ? { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() }
                        : { heading: '', body: b };
        });
        pm_addSwot4Grid(s, C, fonts, hl, sw4Items, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'matrix_2x2') {
        // ── 2×2 포지셔닝 매트릭스 (McKinsey 스타일) ────
        // 라이트 배경 — 데이터 가독성 최우선
        s.background = { color: 'F7F8FA' };
        const _isSerif = (narrativeType === 'B' || narrativeType === 'D');
        const _hlF = _isSerif ? FH : F;

        // 상단 타이틀 바
        s.addShape('rect', { x: 0, y: 0, w: W, h: H * 0.115,
          fill: { color: C.primary.replace('#','') }, line: { type: 'none' } });
        s.addText(eyebrow, { x: W * 0.04, y: 0, w: W * 0.6, h: H * 0.115,
          fontSize: 9, bold: true, color: 'FFFFFF', charSpacing: 3,
          align: 'left', valign: 'middle', fontFace: F });
        s.addText(hl, { x: W * 0.04, y: H * 0.13, w: W * 0.92, h: H * 0.12,
          fontSize: 20, bold: true, color: '111111',
          align: 'left', valign: 'middle', fontFace: _hlF });
        if (sub) s.addText(sub, { x: W * 0.04, y: H * 0.245, w: W * 0.92, h: H * 0.07,
          fontSize: 11, color: '777777', align: 'left', valign: 'middle', fontFace: F });

        // 그리드 좌표
        const gX = W * 0.04, gY = H * 0.32, gW = W * 0.92, gH = H * 0.60;
        const midX = gX + gW / 2, midY = gY + gH / 2;
        const qW = gW / 2 - 0.05, qH = gH / 2 - 0.05;

        // 외곽 테두리
        s.addShape('rect', { x: gX, y: gY, w: gW, h: gH,
          fill: { type: 'none' }, line: { color: 'C8CDD6', width: 1.2 } });
        // 수직 분할선
        s.addShape('rect', { x: midX - 0.007, y: gY, w: 0.014, h: gH,
          fill: { color: 'C8CDD6' }, line: { type: 'none' } });
        // 수평 분할선
        s.addShape('rect', { x: gX, y: midY - 0.007, w: gW, h: 0.014,
          fill: { color: 'C8CDD6' }, line: { type: 'none' } });

        // Q1 (우상단) 강조 배경
        s.addShape('rect', { x: midX, y: gY, w: gW / 2, h: gH / 2,
          fill: { color: C.primary.replace('#',''), transparency: 90 }, line: { type: 'none' } });

        // 사분면 텍스트 (Q1=우상단 Q2=좌상단 Q3=우하단 Q4=좌하단)
        const qCfg = [
          { x: midX + 0.12, y: gY + 0.10 },
          { x: gX + 0.12,   y: gY + 0.10 },
          { x: midX + 0.12, y: midY + 0.10 },
          { x: gX + 0.12,   y: midY + 0.10 },
        ];
        const q4 = body.slice(0, 4).map(b => {
          const ci = b.indexOf(':');
          return ci > 0 ? { label: b.slice(0, ci).trim(), content: b.slice(ci+1).trim() }
                        : { label: '', content: b };
        });
        q4.forEach((qi, qi_idx) => {
          const pos = qCfg[qi_idx];
          const isQ1 = qi_idx === 0;
          if (qi.label) s.addText(qi.label, {
            x: pos.x, y: pos.y, w: qW, h: 0.30,
            fontSize: 12, bold: true, fontFace: _hlF,
            color: isQ1 ? C.primary.replace('#','') : '222222',
            align: 'left', valign: 'top' });
          s.addText(qi.content || '', {
            x: pos.x, y: pos.y + (qi.label ? 0.32 : 0),
            w: qW, h: qH - (qi.label ? 0.32 : 0),
            fontSize: 10, fontFace: F, color: '555555',
            align: 'left', valign: 'top', wrap: true });
        });

        addPageNum('888888');
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'bar_chart') {
        // ── 막대 차트 (수치 데이터 자동 시각화) ─────────
        s.background = { color: 'F7F8FA' };
        const _isSerif = (narrativeType === 'B' || narrativeType === 'D');
        const _hlF = _isSerif ? FH : F;
        const cd = slide.chart_data || {};
        const chartLabels = cd.labels || [];
        const chartValues = (cd.values || []).map(v => Number(v));
        const chartUnit   = cd.unit || '';

        // 상단 타이틀 바
        s.addShape('rect', { x: 0, y: 0, w: W, h: H * 0.115,
          fill: { color: C.primary.replace('#','') }, line: { type: 'none' } });
        s.addText(eyebrow, { x: W * 0.04, y: 0, w: W * 0.6, h: H * 0.115,
          fontSize: 9, bold: true, color: 'FFFFFF', charSpacing: 3,
          align: 'left', valign: 'middle', fontFace: F });
        s.addText(hl, { x: W * 0.04, y: H * 0.13, w: W * 0.92, h: H * 0.12,
          fontSize: 20, bold: true, color: '111111',
          align: 'left', valign: 'middle', fontFace: _hlF });
        if (sub) s.addText(sub, { x: W * 0.04, y: H * 0.245, w: W * 0.92, h: H * 0.07,
          fontSize: 11, color: '777777', align: 'left', valign: 'middle', fontFace: F });

        if (chartLabels.length >= 2 && chartValues.length >= 2) {
          const chartData = [{ name: cd.title || hl, labels: chartLabels, values: chartValues }];
          const fmtCode = chartUnit ? `0"${chartUnit}"` : '0';
          s.addChart(pptx.ChartType.bar, chartData, {
            x: W * 0.04, y: H * 0.34, w: W * 0.92, h: H * 0.56,
            chartColors: [accentHex],
            showLegend: false,
            showValue: true,
            dataLabelFormatCode: fmtCode,
            valAxisHidden: true,
            catAxisLabelFontSize: 12,
            catAxisLabelColor: '444444',
            catAxisLabelFontBold: false,
            barGapWidthPct: 55,
            plotAreaFillColor: 'F7F8FA',
          });
        } else {
          // chart_data 파싱 실패 시 body 기반 kpi_cards로 폴백
          s.addText('데이터를 불러올 수 없습니다.', {
            x: W * 0.04, y: H * 0.40, w: W * 0.92, h: H * 0.20,
            fontSize: 14, color: '888888', align: 'center', fontFace: F });
        }

        addPageNum('888888');
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'linked4') {
        // ── 4개 상호연결 다이어그램 (15p) ────────────────
        const _pmParse = b => {
          b = _stripIcon(b);
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
          const sp = b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, b.length);
          return { heading: b.slice(0, cut).trim(), body: b.slice(cut).trim() };
        };
        const lk4Items = body.length > 0
          ? body.slice(0, 4).map(b => _pmParse(b))
          : [{ heading: hl, body: sub }];
        pm_addLinkedDiagram4(s, C, fonts, hl, lk4Items, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'gear') {
        // ── 기어 프로세스 (18p) ──────────────────────────
        const _pmParse = b => {
          b = _stripIcon(b);
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
          const sp = b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, b.length);
          return { heading: b.slice(0, cut).trim(), body: b.slice(cut).trim() };
        };
        const gearItems = body.length > 0
          ? body.slice(0, 6).map(b => _pmParse(b))
          : [{ heading: hl, body: sub }];
        pm_addGearProcess(s, C, fonts, hl, gearItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'kpi_cards') {
        // ── KPI 대형 숫자 카드 ──────────────────────────
        const _parseKPI = b => {
          // [icon-name] 접두사 추출 (선택적)
          let icon = null, rest = b;
          const iconM = b.match(/^\[([a-z][a-z0-9-]*)\]\s*/);
          if (iconM) { icon = iconM[1]; rest = b.slice(iconM[0].length); }
          // "$3M", "30%", "1.2K" 같은 값 파싱
          const m = rest.match(/^([\$£€]?[\d,.]+\s*[KkMmBbTt%+x×]?\+?)\s*(.*)/s);
          if (m) return { value: m[1].trim(), label: m[2].trim(), icon };
          const ci = rest.indexOf(':');
          if (ci > 0 && ci < 30) return { value: rest.slice(0, ci).trim(), label: rest.slice(ci + 1).trim(), icon };
          const sp = rest.lastIndexOf(' ', 15);
          const cut = sp > 2 ? sp : Math.min(12, rest.length);
          return { value: rest.slice(0, cut).trim(), label: rest.slice(cut).trim(), icon };
        };
        // infographic.data.stats 우선 사용 (proof_results 등에서 정확한 수치 데이터 제공)
        // 빈 값(""/"—") 항목 제거 후 유효 데이터가 있을 때만 사용
        const _statArr = slide.infographic?.data?.stats;
        const _validStats = (_statArr || []).filter(st => {
          const v = String(st.value || '').trim();
          return v && v !== '—' && v !== '-' && v !== 'N/A' && v !== 'n/a';
        });
        const kpiItems = _validStats.length > 0
          ? _validStats.slice(0, 4).map(st => ({
              value: (st.value || '') + (st.unit || ''),
              label: st.label || '',
              icon: null
            }))
          : body.length > 0
            ? body.slice(0, 4).map(b => _parseKPI(b))
            : [{ value: hl, label: sub }];
        pm_addKPICards(s, C, fonts, hl, kpiItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'timeline_bars') {
        // ── 연도별 수평 바 타임라인 ──────────────────────
        const _pmParse2 = b => {
          const _b = b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '');
          const ci = _b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: _b.slice(0, ci).trim(), body: _b.slice(ci + 1).trim() };
          const sp = _b.lastIndexOf(' ', 22);
          const cut = sp > 4 ? sp : Math.min(22, _b.length);
          return { heading: _b.slice(0, cut).trim(), body: _b.slice(cut).trim() };
        };
        const barItems = body.length > 0
          ? body.slice(0, 6).map((b, i) => {
              const p = _pmParse2(b);
              // heading이 연도/숫자면 year로
              const isYear = /^\d{4}$|^Q[1-4]|^\d+년/.test(p.heading);
              return {
                year: isYear ? p.heading : String(2020 + i),
                body: isYear ? p.body : p.heading,
                highlight: i === body.slice(0, 6).length - 1
              };
            })
          : [{ year: '2024', body: hl, highlight: true }];
        pm_addTimelineBars(s, C, fonts, hl, barItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'ruled_list') {
        // ── 수평 구분선 목록 ─────────────────────────────
        const _pmParse3 = b => {
          const _b = b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '');
          const ci = _b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: _b.slice(0, ci).trim(), body: _b.slice(ci + 1).trim() };
          return { heading: _b.trim(), body: '' }; // 콜론 없으면 전체를 제목으로
        };
        const ruleItems = body.length > 0
          ? body.slice(0, 5).map(b => _pmParse3(b))
          : [{ heading: hl, body: sub }];
        pm_addRuledList(s, C, fonts, hl, ruleItems, eyebrow, sub || null);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'problem_solution') {
        // ── 문제(AS-IS) ↔ 해결(TO-BE) 대조 슬라이드 ──
        // slide.before / slide.after 구조 사용 (Gemini problem_solution 타입)
        pm_addProblemSolution(s, C, fonts, hl, slide, eyebrow);
        addLogo(W - 1.60, 0.08, 1.40, 0.44);
        addPageNum(C.textMuted);
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'market_circles') {
        pm_addMarketCircles(s, C, fonts, hl, (() => {
          const _pmi = body.map(b => {
            b = _stripIcon(b);
            const ci = b.indexOf(':');
            if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim() };
            return { heading: b.trim(), body: '' };
          });
          return _pmi.length > 0 ? _pmi : body.map(b => ({ heading: b, body: '' }));
        })(), eyebrow);
        addLogo(W - 1.60, 0.08, 1.40, 0.44);
        addPageNum(C.textMuted);
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'process_cards') {
        // ── Process Cards: 상단 컬러 밴드 카드 (numbered_process 변형) ──
        pm_addProcessCards(s, C, fonts, hl, body, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'numbered_process') {
        // ── 01→02→03→04 체브론 프로세스 ──
        const _pmParse4 = b => {
          // [icon-name] 접두사 추출 (선택적)
          let icon = null, rest = b;
          const iconM = b.match(/^\[([a-z][a-z0-9-]*)\]\s*/);
          if (iconM) { icon = iconM[1]; rest = b.slice(iconM[0].length); }
          const ci = rest.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: rest.slice(0, ci).trim(), body: rest.slice(ci + 1).trim(), icon };
          const sp = rest.lastIndexOf(' ', 20); const cut = sp > 4 ? sp : Math.min(20, rest.length);
          return { heading: rest.slice(0, cut).trim(), body: rest.slice(cut).trim(), icon };
        };
        // infographic.data.steps (flowchart) 우선 사용
        const flowSteps = slide.infographic?.data?.steps;
        const procItems = flowSteps?.length > 0
          ? flowSteps.slice(0, 5).map((st, i) => ({
              heading: st.label || `단계 ${i+1}`,
              body: st.desc || (body[i] ? _pmParse4(body[i]).body : '') || '',
              icon: st.icon || null
            }))
          : body.length > 0
            ? body.slice(0, 5).map(b => _pmParse4(b))
            : [{ heading: hl, body: sub }];
        pm_addNumberedProcess(s, C, fonts, hl, procItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'data_table') {
        // ── 컬러 헤더 + 데이터 행 테이블 ──
        const _parsePipe5 = str => String(str || '').split('|').map(p => p.trim());
        const tblItems = body.length > 0
          ? body.slice(0, 7).map(b => {
              const pi = b.indexOf('|');
              if (pi > 0) return { heading: b.slice(0, pi).trim(), body: b.slice(pi + 1).trim() };
              return { heading: b, body: '' };
            })
          : [{ heading: hl, body: sub }];
        pm_addDataTable(s, C, fonts, hl, tblItems, eyebrow, sub || null);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'stat_3col') {
        // ── 3열 대형 통계 (45%/22%/52% 스타일) ──────────
        const _parseStat = b => {
          b = _stripIcon(b);  // [icon-name] 접두사 제거
          // 숫자 통계 형식: "2000 % A 브랜드 매출 증가"
          const mNum = b.match(/^([\d.,]+)\s*([%배개년M억K+x배×회명]+)\s*(.*)/);
          if (mNum) return { value: mNum[1], unit: mNum[2], label: mNum[3].trim(), desc: '', body: '' };
          // "제목: 설명" 형식 (service_pillar, solution_overview 등)
          const s1 = b.indexOf(': ');
          if (s1 > 0 && s1 <= 22) return { value: '', unit: '', label: b.slice(0, s1).trim(), desc: b.slice(s1 + 2).trim(), body: '' };
          const s2 = b.indexOf(' → ');
          if (s2 > 0 && s2 <= 30) return { value: '', unit: '', label: b.slice(0, s2).trim(), desc: b.slice(s2 + 3).trim(), body: '' };
          // fallback: 전체 텍스트를 label로
          return { value: '', unit: '', label: b, desc: '', body: '' };
        };
        const statItems = slide.infographic?.data?.stats?.length > 0
          ? slide.infographic.data.stats.slice(0, 4)
          : (body.length > 0 ? body.slice(0, 4).map(_parseStat) : [{ value: hl, unit: '', label: sub || '', desc: '' }]);
        pm_addStat3Col(s, C, fonts, hl, statItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'stat_grid') {
        // ── 숫자 그리드 (최대 3×3) ────────────────────
        const _parseStat2 = b => {
          b = _stripIcon(b);  // [icon-name] 접두사 제거
          const m = b.match(/^([\d.,]+)\s*([%배개년M억K+x배×회명]+)\s*(.*)/);
          if (m) return { value: m[1], unit: m[2], label: m[3].trim() };
          return { value: '—', unit: '', label: b };
        };
        const gridItems = slide.infographic?.data?.stats?.length > 0
          ? slide.infographic.data.stats.slice(0, 9)
          : body.slice(0, 9).map(_parseStat2);
        pm_addStatGrid(s, C, fonts, hl, gridItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'timeline_v') {
        // ── 수직 교차 타임라인 ───────────────────────
        const _pmParse = b => {
          b = _stripIcon(b);
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { heading: b.slice(0, ci).trim(), body: b.slice(ci + 1).trim(), date: '' };
          // 연도/날짜 패턴 감지
          const dm = b.match(/^(\d{4}[년.\-/]?(?:\s*\d{1,2}월?)?)\s+(.*)/);
          if (dm) return { date: dm[1].trim(), heading: dm[2].trim(), body: '' };
          return { heading: b, body: '', date: '' };
        };
        const tvItems = body.length > 0
          ? body.slice(0, 6).map(_pmParse)
          : [{ heading: hl, body: sub, date: '' }];
        pm_addVerticalTimeline(s, C, fonts, hl, tvItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'comparison_vs') {
        // ── VS 2열 비교 ──────────────────────────────
        const _pmParse = b => {
          b = _stripIcon(b);
          const ci = b.indexOf(':');
          if (ci > 0 && ci < 30) return { label: b.slice(0, ci).trim(), value: '', unit: '', body: b.slice(ci + 1).trim() };
          const m = b.match(/^(.*?)\s+([\d.,]+)\s*([%배개년M억K+]*)$/);
          if (m) return { label: m[1].trim(), value: m[2], unit: m[3], body: '' };
          return { label: b, value: '', unit: '', body: '' };
        };
        const allItems = body.slice(0, 10).map(_pmParse);
        const half = Math.ceil(allItems.length / 2);
        // groupLabel을 sub에서 추출 ("|" 구분자)
        const grpMatch = (sub || '').split('|');
        const leftGroupLabel = grpMatch[0]?.trim() || 'Option A';
        const rightGroupLabel = grpMatch[1]?.trim() || 'Option B';
        const leftItems  = allItems.slice(0, half).map((it, i) => ({ ...it, groupLabel: i === 0 ? leftGroupLabel : it.label }));
        const rightItems = allItems.slice(half).map((it, i) => ({ ...it, groupLabel: i === 0 ? rightGroupLabel : it.label }));
        pm_addComparisonVS(s, C, fonts, hl, leftItems, rightItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'checklist_pills') {
        // ── G-1: 체크리스트 pill (Brandlogy 참고) ──
        const _cpItems = body.map(b => b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, ''));
        pm_addChecklistPills(s, C, fonts, hl, _cpItems, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'asymmetric_1_3') {
        // ── G-1: Asymmetric 1+3 (좌 대형 + 우 3스택) ──
        pm_addAsymmetric1_3(s, C, fonts, hl, body, eyebrow);
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'pull_quote') {
        // ── Pull Quote — 풀스크린 인용구 ──
        const attribution = sub || '';
        pm_addPullQuote(s, C, fonts, hl, attribution, eyebrow);
        addCopyright('FFFFFF');
        addPageNum('FFFFFF');
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'big_statement') {
        // ── Big Statement — 임팩트 선언 ──
        pm_addBigStatement(s, C, fonts, hl, sub || (body.length > 0 ? body[0] : ''), eyebrow);
        addCopyright();
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'two_col_text') {
        // ── Two Column Text — 좌 제목 + 우 목록 ──
        const _parseTCT = b => {
          const _b = b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '');
          const ci = _b.indexOf(':');
          if (ci > 0 && ci < 35) return { heading: _b.slice(0, ci).trim(), body: _b.slice(ci + 1).trim() };
          const sp = _b.lastIndexOf(' ', 25);
          const cut = sp > 4 ? sp : Math.min(25, _b.length);
          return { heading: _b.slice(0, cut).trim(), body: _b.slice(cut).trim() };
        };
        const tctItems = body.length > 0
          ? body.slice(0, 6).map(b => _parseTCT(b))
          : (sub ? [{ heading: sub, body: '' }] : [{ heading: hl, body: '' }]);
        pm_addTwoColText(s, C, fonts, hl, tctItems, eyebrow, sub);
        addCopyright();
        addPageNum();
        addFavicon();

      // ════════════════════════════════════════════════
      } else if (layout === 'mosaic') {
        // ── Mosaic: 2×2 타일 — 대각선 대칭 (포토+컬러 교차) ──
        const tW = W / 2, tH = H / 2;
        s.background = { color: bgDark };

        // [0,0] 포토 타일 (좌상단)
        s.addShape('rect', { x: 0, y: 0, w: tW, h: tH,
          fill: { color: bgDark }, line: { type: 'none' } });
        if (bgData) {
          s.addImage({ data: bgData, x: 0, y: 0, w: tW, h: tH,
            sizing: { type: 'cover', w: tW, h: tH } });
          s.addShape('rect', { x: 0, y: 0, w: tW, h: tH,
            fill: { color: '000000', transparency: 32 }, line: { type: 'none' } });
        }

        // [0,1] 브랜드 컬러 타일 (우상단) — 헤드라인
        s.addShape('rect', { x: tW, y: 0, w: tW, h: tH,
          fill: { color: C.primary }, line: { type: 'none' } });
        s.addText(hl, {
          x: tW + tW * 0.09, y: tH * 0.16, w: tW * 0.82, h: tH * 0.68,
          fontSize: 24, bold: true, color: 'FFFFFF',
          wrap: true, align: 'left', valign: 'top',
          lineSpacingMultiple: 1.3, fontFace: FH });

        // [1,0] 다크 컬러 타일 (좌하단) — 서브/바디
        const tileBodyStr = body.length > 0
          ? body.slice(0, 3).map(b => '·  ' + b.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, '')).join('\n')
          : (sub || '');
        s.addShape('rect', { x: 0, y: tH, w: tW, h: tH,
          fill: { color: C.accentDark }, line: { type: 'none' } });
        if (tileBodyStr) {
          s.addText(tileBodyStr, {
            x: tW * 0.09, y: tH + tH * 0.12, w: tW * 0.82, h: tH * 0.76,
            fontSize: 16, color: 'FFFFFF',
            wrap: true, align: 'left', valign: 'top',
            lineSpacingMultiple: 1.55, fontFace: F });
        }

        // [1,1] 포토 타일 (우하단) — 같은 이미지
        s.addShape('rect', { x: tW, y: tH, w: tW, h: tH,
          fill: { color: bgDark }, line: { type: 'none' } });
        if (bgData) {
          s.addImage({ data: bgData, x: tW, y: tH, w: tW, h: tH,
            sizing: { type: 'cover', w: tW, h: tH } });
          s.addShape('rect', { x: tW, y: tH, w: tW, h: tH,
            fill: { color: '000000', transparency: 45 }, line: { type: 'none' } });
        }

        // 그리드 교차선 (브랜드 컬러)
        s.addShape('rect', { x: tW - 0.025, y: 0, w: 0.05, h: H,
          fill: { color: C.primary }, line: { type: 'none' } });
        s.addShape('rect', { x: 0, y: tH - 0.025, w: W, h: 0.05,
          fill: { color: C.primary }, line: { type: 'none' } });

        // eyebrow (좌상단 포토 타일 위)
        s.addText(eyebrow, {
          x: tW * 0.07, y: tH * 0.07, w: tW * 0.86, h: tH * 0.12,
          fontSize: 11, bold: true, color: 'FFFFFF',
          charSpacing: 3, valign: 'top', fontFace: F });

        // sub (우하단 포토 타일)
        if (sub && body.length > 0) {
          s.addText(sub, {
            x: tW + tW * 0.09, y: tH + tH * 0.12, w: tW * 0.82, h: tH * 0.35,
            fontSize: 18, color: 'FFFFFF',
            wrap: true, align: 'left', valign: 'top',
            lineSpacingMultiple: 1.3, fontFace: F });
        }

        addPageNum('CCCCCC');
        addFavicon();

      // ════════════════════════════════════════════════
      } else {
        // ── 마지막 슬라이드 (Contact) 또는 CTA 슬라이드 ──
        if (isLastSlide) {
          // ── Contact page (Last Slide) — Redesigned ──
          s.background = { color: C.tintedDark || '111111' };

          // 은은한 데코 (질감만 살림)
          s.addShape('ellipse', { x: W * 0.15, y: -H * 0.40, w: H * 1.80, h: H * 1.80,
            fill: { color: C.primary, transparency: 96 }, line: { type: 'none' } });

          // 1. 브랜드/로고 (중앙 대형)
          if (showLogo && logoAspect && logoAspect >= 1.0) {
            const maxLgW = 5.0, maxLgH = 1.2;
            let lgW, lgH;
            if (logoAspect >= maxLgW / maxLgH) { lgW = maxLgW; lgH = maxLgW / logoAspect; }
            else { lgH = maxLgH; lgW = maxLgH * logoAspect; }
            s.addImage({ data: `data:image/${logoMime};base64,${logoB64}`,
                         x: (W - lgW) / 2, y: H * 0.22, w: lgW, h: lgH });
          } else {
            s.addText((companyName || '').toUpperCase(), {
              x: W * 0.10, y: H * 0.20, w: W * 0.80, h: 1.2,
              fontSize: 58, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle',
              fontFace: FH, charSpacing: 4 });
          }

          // 2. 헤드라인 (Closing Message)
          s.addText(hl || 'Thank you.', {
            x: W * 0.10, y: H * 0.44, w: W * 0.80, h: 0.60,
            fontSize: 22, color: C.tintedGray || 'CCCCCC', align: 'center', valign: 'top',
            fontFace: F });

          // 3. 연락처 정보 (2열 레이아웃)
          const contactItems = body.filter(b => {
              if (/사업자|등록번호|business.*reg|tax.*num/i.test(b)) return false;
              if (b.trim().length > 120) return false;
              if (b.trim().length < 2) return false;
              return true;
          }).slice(0, 4);

          if (contactItems.length > 0) {
            const ctrlW = W * 0.70;
            const ctrlX = (W - ctrlW) / 2;
            const colW  = ctrlW / 2;
            contactItems.forEach((item, idx) => {
              const ix = ctrlX + (idx % 2) * colW;
              const iy = H * 0.62 + Math.floor(idx / 2) * 0.50;
              s.addText(item, {
                x: ix, y: iy, w: colW, h: 0.40,
                fontSize: 12.5, color: 'FFFFFF', align: 'center', valign: 'middle',
                fontFace: F, transparency: 15 });
            });
          }

          // 4. 하단 그라데이션 바
          try {
            s.addShape('rect', { x: 0, y: H - 0.08, w: W, h: 0.08,
              fill: { type: 'gradient', color: [C.primary, C.accentLight], angle: 0 }, line: { type: 'none' } });
          } catch(e) {
            s.addShape('rect', { x: 0, y: H - 0.08, w: W, h: 0.08,
              fill: { color: C.primary }, line: { type: 'none' } });
          }

          addCopyright('888888', (W - 6) / 2);
          addPageNum('888888');

        } else {
          // ── CTA Slide — Redesigned ──
          s.background = { color: C.tintedDark || '111111' };

          // 은은한 데코
          s.addShape('ellipse', { x: -W * 0.15, y: -H * 0.20, w: H * 1.2, h: H * 1.2,
            fill: { color: C.primary, transparency: 88 }, line: { type: 'none' } });

          // 1. Eyebrow
          if (eyebrow) {
            s.addText(eyebrow.toUpperCase(), {
              x: 0, y: H * 0.14, w: W, h: 0.30,
              fontSize: 11, bold: true, color: C.primary, charSpacing: 4, align: 'center', fontFace: F });
          }

          // 2. Headline
          s.addText(hl, {
            x: W * 0.10, y: H * 0.22, w: W * 0.80, h: 1.0,
            fontSize: 42, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle',
            fontFace: FD, lineSpacingMultiple: 1.2 });

          // 3. Subheadline (No Box)
          if (sub) {
            s.addText(sub, {
              x: W * 0.10, y: H * 0.40, w: W * 0.80, h: 0.50,
              fontSize: 18, color: C.tintedGray || 'CCCCCC', align: 'center', valign: 'top',
              fontFace: F });
          }

          // 4. 3-Column Cards with Numbers
          const ctaItems = body.slice(0, 3);
          if (ctaItems.length > 0) {
            const gridW = W * 0.85;
            const cardGap = 0.40;
            const cardW = (gridW - cardGap * (ctaItems.length - 1)) / ctaItems.length;
            const startX = (W - gridW) / 2;
            
            ctaItems.forEach((item, idx) => {
              const cx = startX + idx * (cardW + cardGap);
              const cy = H * 0.54;
              const ch = 1.62;

              // Card background (transparency 90, 0.5px border)
              s.addShape('roundRect', {
                x: cx, y: cy, w: cardW, h: ch,
                fill: { color: 'FFFFFF', transparency: 90 },
                line: { color: C.primary, transparency: 30, width: 0.5 },
                rectRadius: 0.12
              });

              // Number (01, 02, 03)
              s.addText(String(idx + 1).padStart(2, '0'), {
                x: cx, y: cy + 0.12, w: cardW, h: 0.35,
                fontSize: 14, bold: true, color: C.primary, align: 'center', fontFace: F });

              // Item Text
              s.addText(item.replace(/^\[[a-z][a-z0-9-]*\]\s*/i, ''), {
                x: cx + 0.12, y: cy + 0.48, w: cardW - 0.24, h: ch - 0.60,
                fontSize: 13, color: 'FFFFFF', align: 'center', valign: 'top',
                fontFace: F, wrap: true, lineSpacingMultiple: 1.3 });
            });
          }

          // 5. 하단 그라데이션 바
          try {
            s.addShape('rect', { x: 0, y: H - 0.08, w: W, h: 0.08,
              fill: { type: 'gradient', color: [C.primary, C.accentLight], angle: 0 }, line: { type: 'none' } });
          } catch(e) {
            s.addShape('rect', { x: 0, y: H - 0.08, w: W, h: 0.08,
              fill: { color: C.primary }, line: { type: 'none' } });
          }

          addCopyright('888888', (W - 6) / 2);
          addFavicon();
          addPageNum('888888');
        } // end else (CTA, not last)
      }

      // ── 커버 제외 카피라이트 누락 보정 ──
      if (!_cpDone && layout !== 'cover') {
        const _isDark = ['portfolio','pull_quote','big_statement','cta'].includes(layout) || !!bgData;
        addCopyright(_isDark ? 'FFFFFF' : '888888');
      }

      // ── 하단 quote strip (slide.quote 있을 때 공통) ──
      if (slide.quote && !['cover','cta','toc','section'].includes(layout)) {
        const qY = H * 0.845, qH = H * 0.14;
        s.addShape('rect', { x: 0, y: qY, w: W, h: qH,
          fill: { color: '000000', transparency: 25 }, line: { type: 'none' } });
        s.addShape('rect', { x: 0, y: qY, w: 0.055, h: qH,
          fill: { color: C.primary }, line: { type: 'none' } });
        s.addText('\u201C' + String(slide.quote) + '\u201D', {
          x: 0.22, y: qY + 0.02, w: W - 0.35, h: qH - 0.04,
          fontFace: F, fontSize: 11, color: 'EEEEEE',
          align: 'left', valign: 'middle', italic: true, wrap: true });
      }
    }

    // Blob 반환 (PDF 변환용) 또는 직접 다운로드
    if (data._returnBlob) {
      return await pptx.write({ outputType: 'blob' });
    }
    const fileName = `${meta.company_name || 'slides'}_slides.pptx`;
    await pptx.writeFile({ fileName });
  }
