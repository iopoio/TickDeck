export interface SlideItem {
  type: string
  headline: string
  subheadline: string
  eyebrow: string
  body: string[]
}

export interface BrandInfo {
  companyName: string
  primaryColor: string
  industry: string
}

export interface SlideContent {
  brand: BrandInfo
  slides: SlideItem[]
  language: string
}

export interface GenerationStatus {
  generation_id: string
  status: 'pending' | 'crawling' | 'structuring' | 'ready_to_edit' | 'building_pptx' | 'done' | 'failed'
  slide_content: SlideContent | null
  error_message: string | null
  pptx_url: string | null
}
