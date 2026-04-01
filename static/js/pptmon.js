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

