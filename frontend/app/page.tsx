"use client"

import { useState, useEffect, useRef } from "react"
import { Plus, Minus, X, Check, Loader2, AlertCircle, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { useDropzone } from "react-dropzone"
import PHONE_CATALOG from "../data/phoneCatalog"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://listing-bot-api-production.up.railway.app"
const PROXY_BASE = "/api" // Next.js API proxy

// Comprehensive options for all fields
const CATEGORIES = {
  phones: ["Smartphones", "Feature Phones", "Tablets"],
  accessories: [
    "Antennas", "Batteries", "Bluetooth", "Boxes", "Broadband Cards",
    "Car Chargers", "Car Kits", "Chargers", "Covers", "Data Cables",
    "Digitizers", "Displays", "Electric Vehicles", "GPS Modules",
    "Headsets", "Holsters", "Housing Cases", "Jewellery", "Keyboards",
    "Mainboards", "MicroSD Cards", "Mounts", "Novelties", "Others",
    "Prepay Cards", "Screen Protectors", "Signal Boosters", "SIM Cards",
    "Spare Parts", "USB Modems", "VR Headsets"
  ],
  gadgets: [
    "Accessories", "Camera & Photo", "Car Multimedia", "Computers",
    "Drones", "Gadgets", "Gaming Consoles", "GPS Navigation",
    "Home Multimedia", "IoT", "Kitchen Tools", "Medical & Health",
    "MP3 Players", "Networking", "Other", "PC Components",
    "Power Tools", "Sport & Fitness", "TV & Satellite", "Video Cards"
  ]
}

const CONDITIONS = ["New", "Used", "Refurbished", "Damaged", "14-Days"]
const CONDITION_GRADES = ["A", "B", "C", "D"]
const LCD_DEFECTS = ["None", "Spot", "Line", "Light Burn-in", "Noticeable Burn-in"]
const MEMORY_OPTIONS = ["4GB", "8GB", "16GB", "32GB", "64GB", "128GB", "256GB", "512GB", "1TB", "2TB"]
const COLORS = [
  "Black", "White", "Gray", "Silver", "Blue", "Gold", "Green", "Red",
  "Yellow", "Pink", "Purple", "Brown", "Champagne", "Rose Gold",
  "Mix Colors", "Graphite", "Other"
]
const MARKET_SPECS = ["US", "Euro", "UK", "Asia", "Arabic", "Other"]
const SIM_LOCK_STATUS = ["Never Locked", "Unlocked", "Locked"]
const PACKAGING_OPTIONS = [
  "Any Pack", "Original Box", "Operator Box", "White Box",
  "Bulk Packed", "Blister Packed", "Other"
]
const INCOTERMS = ["EXW", "FOB", "CIF", "DDP", "FCA", "CPT", "CIP", "DAF"]
const PAYMENT_METHODS = ["Wire TT", "PayPal", "COD", "Amazon Pay"]
const WEIGHT_UNITS = ["kg", "lbs"]
const CURRENCIES = ["USD", "EUR", "GBP", "CNY", "JPY"]

type PlatformStatus = "pending" | "posting" | "success" | "error"

type ComprehensiveListingItem = {
  id: string
  // Basic Info
  productType: "phone" | "accessory" | "gadget"
  category: string
  brand: string
  productName: string
  modelCode: string
  
  // Condition & Quality
  condition: string
  customCondition: string
  conditionGrade: string
  lcdDefects: string
  qualityCertification: string
  
  // Technical Specs
  memory: string
  color: string
  marketSpec: string
  simLockStatus: string
  carrier: string
  
  // Pricing & Inventory
  price: number
  currency: string
  quantity: number
  minimumOrderQuantity: number
  supplyAbility: string
  
  // Shipping & Packaging
  packaging: string
  itemWeight: number
  weightUnit: string
  incoterm: string
  allowLocalPickup: boolean
  deliveryDays: number
  
  // Location
  country: string
  state: string
  
  // Description & Media
  description: string
  keywords: string[]
  photos: File[]
  photoUrls: string[]
  
  // Payment & Sharing
  acceptedPayments: string[]
  autoShareLinkedIn: boolean
  autoShareTwitter: boolean
  
  // Platform Selection
  selectedPlatforms: string[]
  platformStatuses: Record<string, { status: PlatformStatus; message?: string }>
  
  // Additional
  privateNotes: string
  manufacturerType: "OEM" | "ODM" | "not_specified"
}

function DragDropCsv({ onFile, children }: { onFile: (f: File) => void, children: React.ReactNode }) {
  const onDrop = (accepted: File[]) => {
    const file = accepted?.[0]
    if (file) onFile(file)
  }
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'text/csv': ['.csv'] } })
  return (
    <div {...getRootProps()} className={`mr-4 rounded-md border px-4 py-3 cursor-pointer ${isDragActive ? 'bg-accent/40' : 'bg-background'}`}>
      <input {...getInputProps()} />
      {children}
    </div>
  )
}

export default function ListingBotUI() {
  const [items, setItems] = useState<ComprehensiveListingItem[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  type PhoneEntry = { brand: string; model: string; label: string }
  const [productSuggestions, setProductSuggestions] = useState<string[]>([])
  const [phoneCatalog, setPhoneCatalog] = useState<PhoneEntry[]>([])
  const [activeSuggestItemId, setActiveSuggestItemId] = useState<string | null>(null)
  const [gmailStatus, setGmailStatus] = useState<"unknown" | "authenticated" | "requires_auth" | "not_configured">("unknown")
  const [gmailRefreshToken, setGmailRefreshToken] = useState<string>("")
  const lastWarmupRef = useRef<number>(0)

  const warmupServer = async () => {
    try {
      const now = Date.now()
      if (now - (lastWarmupRef.current || 0) < 30000) return
      // Warm both upstream and the proxy route
      await fetch(`${PROXY_BASE}/listings/enhanced-visual`, { method: "GET", cache: "no-store" })
      await fetch(`${API_BASE_URL}/`, { method: "GET", cache: "no-store" })
      lastWarmupRef.current = now
    } catch {}
  }

  // Global debug hooks to surface silent errors
  useEffect(() => {
    const onErr = (e: ErrorEvent) => {
      // Avoid crashing UI on unexpected errors
      // eslint-disable-next-line no-console
      console.error("Global error captured:", e?.error || e?.message, e)
    }
    const onRej = (e: PromiseRejectionEvent) => {
      // eslint-disable-next-line no-console
      console.error("Unhandled promise rejection:", e?.reason)
    }
    window.addEventListener("error", onErr)
    window.addEventListener("unhandledrejection", onRej)
    // Initial heartbeat
    // eslint-disable-next-line no-console
    console.info("🟢 Listing UI mounted and ready")
    return () => {
      window.removeEventListener("error", onErr)
      window.removeEventListener("unhandledrejection", onRej)
    }
  }, [])

  useEffect(() => {
    const saved = localStorage.getItem("productSuggestions")
    if (saved) {
      setProductSuggestions(JSON.parse(saved))
    }
    // Hydrate phone catalog from public datasets (Android certified devices) when available
    ;(async () => {
      try {
        // Prefer V2 cache with structured entries
        const cachedV2 = localStorage.getItem("phoneCatalogCacheV2")
        if (cachedV2) {
          try {
            const parsed = JSON.parse(cachedV2)
            if (Array.isArray(parsed?.data) && parsed.data.length >= 500) {
              setPhoneCatalog(parsed.data)
              return
            }
          } catch {}
        }
        // Fallback: try legacy cache and convert to entries
        const cachedLegacy = localStorage.getItem("phoneCatalogCache")
        if (cachedLegacy) {
          try {
            const parsed = JSON.parse(cachedLegacy)
            if (Array.isArray(parsed?.data) && parsed.data.length >= 500) {
              const converted: PhoneEntry[] = (parsed.data as string[]).map((label: string) => {
                const parts = (label || "").trim().split(/\s+/)
                const brand = parts.shift() || ""
                const model = parts.join(" ")
                return { brand, model, label }
              })
              setPhoneCatalog(converted)
              localStorage.setItem("phoneCatalogCacheV2", JSON.stringify({ ts: Date.now(), data: converted }))
              return
            }
          } catch {}
        }
        const CATALOG_SOURCES = [
          // Gist with certified Android devices (fallback mirror)
          "https://gist.githubusercontent.com/noamtamim/9ecee1ead83e6a9541d4c194a88f8e89/raw/devices.json",
          // Historical androidtrackers path (may 404, kept as secondary)
          "https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/devices.json"
        ] as const

        const parseCatalog = async (res: Response): Promise<PhoneEntry[] | null> => {
          try {
            const text = await res.text()
            // Try JSON first
            try {
              const json = JSON.parse(text)
              const entries: PhoneEntry[] = []
              const seen = new Set<string>()
              if (Array.isArray(json)) {
                for (let i = 0; i < json.length; i++) {
                  const item = json[i] as any
                  const brand = (item?.brand || item?.Brand || item?.manufacturer || "").toString().trim()
                  const name = (item?.name || item?.Name || item?.model || "").toString().trim()
                  if (!brand || !name) continue
                  const label = `${brand} ${name}`.replace(/\s+/g, " ").trim()
                  const key = `${brand.toLowerCase()}|${name.toLowerCase()}`
                  if (label.length >= 3 && !seen.has(key)) {
                    seen.add(key)
                    entries.push({ brand, model: name, label })
                  }
                }
              } else if (json && typeof json === "object") {
                // Some datasets map brand -> [models]
                for (const [brandKey, arr] of Object.entries(json as Record<string, any>)) {
                  if (!Array.isArray(arr)) continue
                  const brand = (brandKey || "").toString().trim()
                  for (const model of arr) {
                    const name = (model || "").toString().trim()
                    if (!brand || !name) continue
                    const label = `${brand} ${name}`.replace(/\s+/g, " ").trim()
                    const key = `${brand.toLowerCase()}|${name.toLowerCase()}`
                    if (label.length >= 3 && !seen.has(key)) {
                      seen.add(key)
                      entries.push({ brand, model: name, label })
                    }
                  }
                }
              }
              if (entries.length) return entries
            } catch {}
            // Try CSV as a secondary parse path
            try {
              const lines = text.split(/\r?\n/).filter(Boolean)
              if (lines.length > 5) {
                const entries: PhoneEntry[] = []
                const seen = new Set<string>()
                for (const line of lines.slice(1)) {
                  const cols = line.split(",")
                  const brand = (cols[0] || "").trim()
                  const name = (cols[1] || "").trim()
                  if (!brand || !name) continue
                  const label = `${brand} ${name}`
                  const key = `${brand.toLowerCase()}|${name.toLowerCase()}`
                  if (!seen.has(key)) {
                    seen.add(key)
                    entries.push({ brand, model: name, label })
                  }
                }
                if (entries.length) return entries
              }
            } catch {}
            return null
          } catch { return null }
        }

        let hydrated = false
        for (const url of CATALOG_SOURCES) {
          try {
            const res = await fetch(url, { cache: "no-store" })
            if (!res.ok) continue
            const entries = await parseCatalog(res)
            if (entries && entries.length >= 500) {
              entries.sort((a, b) => a.label.localeCompare(b.label))
              setPhoneCatalog(entries)
              localStorage.setItem("phoneCatalogCacheV2", JSON.stringify({ ts: Date.now(), data: entries }))
              hydrated = true
              break
            }
          } catch {
            // try next source
          }
        }
        if (!hydrated) {
          // Final fallback to bundled list to ensure autocomplete works
          const fallback: PhoneEntry[] = (PHONE_CATALOG as unknown as string[]).map((label) => {
            const parts = (label || "").trim().split(/\s+/)
            const brand = parts.shift() || ""
            const model = parts.join(" ")
            return { brand, model, label }
          })
          setPhoneCatalog(fallback)
          localStorage.setItem("phoneCatalogCacheV2", JSON.stringify({ ts: Date.now(), data: fallback }))
        }
      } catch {
        // Ignore network errors; rely on bundled PHONE_CATALOG
        try {
          // Convert bundled fallback strings to structured entries
          const fallback: PhoneEntry[] = (PHONE_CATALOG as unknown as string[]).map((label) => {
            const parts = (label || "").trim().split(/\s+/)
            const brand = parts.shift() || ""
            const model = parts.join(" ")
            return { brand, model, label }
          })
          setPhoneCatalog(fallback)
        } catch {}
      }
    })()
    // Persist suggestions across sessions
    // Load Gmail auth status on mount
    ;(async () => {
      try {
        const res = await fetch(`/api/gmail/status`)
        const data = await res.json()
        if (data?.status) setGmailStatus(data.status)
      } catch {
        setGmailStatus("not_configured")
      }
    })()
  }, [])

  const startGmailOAuth = async () => {
    try {
      // Ask backend to redirect directly (avoids popup blockers and JSON parsing issues)
      window.location.href = `/api/gmail/auth?redirect=true`
    } catch (e) {
      console.error("Failed to start Gmail OAuth", e)
    }
  }

  const fetchGmailRefreshToken = async () => {
    try {
      const res = await fetch(`/api/gmail/refresh-token`)
      const data = await res.json()
      if (data?.refresh_token) setGmailRefreshToken(data.refresh_token)
      // Also refresh status
      const s = await fetch(`${API_BASE_URL}/gmail/status`).then(r => r.json())
      if (s?.status) setGmailStatus(s.status)
    } catch (e) {
      console.error("Failed to fetch refresh token", e)
    }
  }

  const addNewItem = () => {
    const newItem: ComprehensiveListingItem = {
      id: Date.now().toString(),
      productType: "phone",
      category: "Smartphones",
      brand: "",
      productName: "",
      modelCode: "",
      condition: "New",
      customCondition: "",
      conditionGrade: "A",
      lcdDefects: "None",
      qualityCertification: "",
      memory: "128GB",
      color: "Black",
      marketSpec: "US",
      simLockStatus: "Unlocked",
      carrier: "",
      price: 0,
      currency: "USD",
      quantity: 1,
      minimumOrderQuantity: 1,
      supplyAbility: "",
      packaging: "Original Box",
      itemWeight: 0.3,
      weightUnit: "kg",
      incoterm: "EXW",
      allowLocalPickup: false,
      deliveryDays: 7,
      country: "United States",
      state: "",
      description: "",
      keywords: [],
      photos: [],
      photoUrls: [],
      acceptedPayments: ["PayPal"],
      autoShareLinkedIn: false,
      autoShareTwitter: false,
      selectedPlatforms: [],
      platformStatuses: {},
      privateNotes: "",
      manufacturerType: "not_specified"
    }
    setItems([...items, newItem])
  }

  const fillExampleData = (itemId: string) => {
    const exampleData = {
      productType: "phone" as const,
      category: "Smartphones",
      brand: "Apple",
      productName: "iPhone 14 Pro",
      modelCode: "A2890",
      condition: "Used",
      customCondition: "",
      conditionGrade: "A",
      lcdDefects: "None",
      qualityCertification: "CE, FCC, IC",
      memory: "256GB",
      color: "Deep Purple",
      marketSpec: "US",
      simLockStatus: "Unlocked",
      carrier: "AT&T",
      price: 899.99,
      currency: "USD",
      quantity: 5,
      minimumOrderQuantity: 1,
      supplyAbility: "100 units/month",
      packaging: "Original Box",
      itemWeight: 0.206,
      weightUnit: "kg",
      incoterm: "EXW",
      allowLocalPickup: true,
      deliveryDays: 3,
      country: "United States",
      state: "California",
      description: "Premium iPhone 14 Pro in excellent condition. Features the powerful A16 Bionic chip, Pro camera system with 48MP main camera, and stunning Super Retina XDR display. Unlocked and ready to use with any carrier. Includes original box, charging cable, and documentation.",
      keywords: ["iPhone", "Apple", "smartphone", "unlocked", "256GB", "Deep Purple", "A16", "Pro camera"],
      acceptedPayments: ["PayPal", "Wire TT"],
      autoShareLinkedIn: false,
      autoShareTwitter: false,
      selectedPlatforms: ["gsmexchange", "cellpex"],
      privateNotes: "High-demand model, excellent margins",
      manufacturerType: "OEM" as const
    }
    
    updateItem(itemId, exampleData)
    
    // Show a quick confirmation
    console.log("✅ Example data filled! Ready for testing.")
  }

  const updateItem = (id: string, updates: Partial<ComprehensiveListingItem>) => {
    setItems(items.map(item => (item.id === id ? { ...item, ...updates } : item)))
  }

  const removeItem = (id: string) => {
    setItems(items.filter(item => item.id !== id))
  }

  const handlePhotoUpload = (itemId: string, files: FileList) => {
    const item = items.find(i => i.id === itemId)
    if (!item) return

    const newPhotos = Array.from(files)
    const photoUrls = newPhotos.map(file => URL.createObjectURL(file))
    
    updateItem(itemId, {
      photos: [...item.photos, ...newPhotos],
      photoUrls: [...item.photoUrls, ...photoUrls]
    })

    // Call AI to generate description and keywords from photos
    generateAIContent(itemId, newPhotos)
  }

  const generateAIContent = async (itemId: string, photos: File[]) => {
    // This would call your AI service to analyze photos and generate content
    // For now, we'll simulate it with console.log instead of toast
    console.log("AI Analysis: Analyzing photos to generate description and keywords...")

    // Simulate AI processing
    setTimeout(() => {
      const item = items.find(i => i.id === itemId)
      if (!item) return

      updateItem(itemId, {
        description: `Professional ${item.productName} in ${item.condition.toLowerCase()} condition. ${item.memory} storage, ${item.color.toLowerCase()} color variant.`,
        keywords: [item.brand, item.productName, item.memory, item.color, item.condition].filter(Boolean)
      })

      console.log("AI Complete: Description and keywords generated!")
    }, 2000)
  }

  const submitForProcessing = async () => {
    if (items.length === 0) {
      alert("Please add at least one item to process")
      return
    }

    setIsProcessing(true)

    const debugRunId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    // eslint-disable-next-line no-console
    console.group(`🚀 Submit run ${debugRunId}`)
    // eslint-disable-next-line no-console
    console.log("Items count:", items.length)

    for (const item of items) {
      if (item.selectedPlatforms.length === 0) continue

      // Process platforms in parallel
      const platformPromises = item.selectedPlatforms.map(async (platformId) => {
        // eslint-disable-next-line no-console
        console.group(`▶️ Start ${platformId} for item ${item.productName || item.id}`)
        updateItem(item.id, {
          platformStatuses: {
            ...item.platformStatuses,
            [platformId]: { status: "posting" },
          },
        })

        try {
          const payload = {
            platform: platformId,
            listing_data: {
              // Send all the comprehensive data
              product_type: item.productType,
              // Hint backend about Cellpex section mapping
              section: item.productType === "accessory" ? "2" : (item.productType === "gadget" ? "G" : "1"),
              category: item.category,
              brand: item.brand,
              product_name: item.productName,
              model_code: item.modelCode,
              condition: item.condition === "other" ? item.customCondition : item.condition,
              condition_grade: item.conditionGrade,
              lcd_defects: item.lcdDefects,
              quality_certification: item.qualityCertification,
              memory: item.memory,
              color: item.color,
              market_spec: item.marketSpec,
              sim_lock_status: item.simLockStatus,
              carrier: item.carrier,
              price: item.price,
              currency: item.currency,
              quantity: item.quantity,
              minimum_order_quantity: item.minimumOrderQuantity,
              supply_ability: item.supplyAbility,
              packaging: item.packaging,
              item_weight: item.itemWeight,
              weight_unit: item.weightUnit,
              incoterm: item.incoterm,
              allow_local_pickup: item.allowLocalPickup,
              delivery_days: item.deliveryDays,
              country: item.country,
              state: item.state,
              description: item.description,
              keywords: item.keywords,
              accepted_payments: item.acceptedPayments,
              auto_share_linkedin: item.autoShareLinkedIn,
              auto_share_twitter: item.autoShareTwitter,
              private_notes: item.privateNotes,
              manufacturer_type: item.manufacturerType
            }
          }

          // eslint-disable-next-line no-console
          console.debug("↗️ Request:", { platformId, payload: { ...payload, listing_data: { ...payload.listing_data, description: (payload.listing_data.description || "").slice(0, 80) + "…", keywords_len: payload.listing_data.keywords?.length } } })

          const doRequest = async () => {
            // Hit proxy to avoid browser HTTP/2 issues
            return await fetch(`${PROXY_BASE}/listings/enhanced-visual`, {
              method: "POST",
              headers: { "Content-Type": "application/json", "Accept": "application/json" },
              cache: "no-store",
              referrerPolicy: "no-referrer",
              body: JSON.stringify(payload),
            })
          }
          // Retry with exponential backoff for transient network errors
          let response: Response | null = null
          let lastErr: any = null
          await warmupServer()
          for (let attempt = 0; attempt < 5; attempt++) {
            try {
              response = await doRequest()
              if (response.ok) break
              lastErr = new Error(`HTTP ${response.status}`)
            } catch (e) {
              lastErr = e
            }
            await new Promise(r => setTimeout(r, 400 * (attempt + 1)))
            if (attempt === 0 || attempt === 2) await warmupServer()
          }
          if (!response) throw lastErr || new Error("Network error")

          const raw = await response.text()
          let result: any
          try {
            result = raw ? JSON.parse(raw) : {}
          } catch (e) {
            // eslint-disable-next-line no-console
            console.error("❌ Failed to parse JSON response", { status: response.status, raw: raw?.slice(0, 2000) })
            throw e
          }

          // eslint-disable-next-line no-console
          console.debug("↙️ Response:", { status: response.status, ok: response.ok, keys: Object.keys(result || {}) })

          // Log browser automation steps for visualization
          if (result.browser_steps) {
            // eslint-disable-next-line no-console
            console.group(`🌐 Browser Automation: ${platformId}`)
            ;(Array.isArray(result.browser_steps) ? result.browser_steps : [result.browser_steps]).forEach((step: any, idx: number) => {
              const emoji = step.status === 'success' ? '✅' : 
                           step.status === 'error' ? '❌' : 
                           step.status === 'action_required' ? '⚠️' : '⏳'
              // eslint-disable-next-line no-console
              console.log(`${emoji} ${step.message || '(no message)'} [${idx}]`)
              if (step.requires_2fa) {
                // eslint-disable-next-line no-console
                console.log('🔐 2FA Required - Checking email for verification code...')
              }
              if (step.fields_filled) {
                try {
                  const tableData = step.fields_filled && typeof step.fields_filled === 'object' ? step.fields_filled : { value: step.fields_filled }
                  // eslint-disable-next-line no-console
                  console.table(tableData as any)
                } catch (err) {
                  // eslint-disable-next-line no-console
                  console.warn('⚠️ console.table failed for fields_filled', err)
                }
              }
            })
            // eslint-disable-next-line no-console
            console.groupEnd()
          }

          updateItem(item.id, {
            platformStatuses: {
              ...item.platformStatuses,
              [platformId]: {
                status: result.success ? "success" : "error",
                message: result.message,
              },
            },
          })
          // eslint-disable-next-line no-console
          console.groupEnd()
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error(`❌ ${platformId} failed`, error)
          updateItem(item.id, {
            platformStatuses: {
              ...item.platformStatuses,
              [platformId]: {
                status: "error",
                message: error instanceof Error ? error.message : "Network error",
              },
            },
          })
          // eslint-disable-next-line no-console
          console.groupEnd()
        }
      })

      // Wait for all platforms to complete for this item
      await Promise.all(platformPromises)
      // eslint-disable-next-line no-console
      console.log(`✨ All platforms processed for ${item.productName}`)
    }

    setIsProcessing(false)
    // eslint-disable-next-line no-console
    console.groupEnd()
    // eslint-disable-next-line no-console
    console.log('🎯 All items and platforms processed!')
  }

  const downloadExampleSheet = () => {
    const header = [
      'productType','category','brand','productName','modelCode','condition','memory','color','marketSpec','simLockStatus','carrier','price','currency','quantity','minimumOrderQuantity','supplyAbility','packaging','itemWeight','weightUnit','incoterm','allowLocalPickup','deliveryDays','country','state','description','keywords'
    ]
    const rows = [
      ['phone','Smartphones','Apple','iPhone 14 Pro','A2890','New','256GB','Black','US','Unlocked','AT&T',999,'USD',10,1,'','Original Box',0.3,'kg','EXW',false,7,'United States','California','Premium device','Apple;iPhone;14 Pro']
    ]
    const csv = [header.join(','), ...rows.map(r=>r.map(v=>typeof v==='string' && v.includes(',')?`"${v}"`:v).join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'listing_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  // CSV upload state and helpers
  const requiredHeaders = ['productType','category','brand','productName','modelCode','condition','price','currency','quantity','country']
  const [csvPreview, setCsvPreview] = useState<{ headers: string[], rows: string[][] }>({ headers: [], rows: [] })
  const [csvErrors, setCsvErrors] = useState<string[]>([])

  const parseCsvText = (text: string) => {
    const lines = text.split(/\r?\n/).filter(Boolean)
    const headers = lines.length ? lines[0].split(',').map(h => h.trim()) : []
    const rows = lines.slice(1).map(l => l.split(','))
    return { headers, rows }
  }

  const handleCsvFile = async (file: File) => {
    const text = await file.text()
    const { headers, rows } = parseCsvText(text)
    const missing = requiredHeaders.filter(h => !headers.includes(h))
    setCsvErrors(missing.length ? [`Missing required headers: ${missing.join(', ')}`] : [])
    setCsvPreview({ headers, rows })
  }

  const createItemsFromPreview = () => {
    const { headers, rows } = csvPreview
    if (!headers.length || !rows.length) return
    const missing = requiredHeaders.filter(h => !headers.includes(h))
    if (missing.length) {
      alert(`Missing required headers: ${missing.join(', ')}`)
      return
    }
    const idx = (h: string) => headers.indexOf(h)
    const newItems: ComprehensiveListingItem[] = rows.map((cols) => ({
      id: `${Date.now()}-${Math.random().toString(36).slice(2,8)}`,
      productType: (cols[idx('productType')] as any) || 'phone',
      category: cols[idx('category')] || '',
      brand: cols[idx('brand')] || '',
      productName: cols[idx('productName')] || '',
      modelCode: cols[idx('modelCode')] || '',
      condition: cols[idx('condition')] || 'New',
      customCondition: '',
      conditionGrade: 'A',
      lcdDefects: 'None',
      qualityCertification: '',
      memory: cols[idx('memory')] || '128GB',
      color: cols[idx('color')] || 'Black',
      marketSpec: cols[idx('marketSpec')] || 'US',
      simLockStatus: cols[idx('simLockStatus')] || 'Unlocked',
      carrier: cols[idx('carrier')] || '',
      price: parseFloat(cols[idx('price')] || '0') || 0,
      currency: cols[idx('currency')] || 'USD',
      quantity: parseInt(cols[idx('quantity')] || '1') || 1,
      minimumOrderQuantity: parseInt(cols[idx('minimumOrderQuantity')] || '1') || 1,
      supplyAbility: cols[idx('supplyAbility')] || '',
      packaging: cols[idx('packaging')] || 'Original Box',
      itemWeight: parseFloat(cols[idx('itemWeight')] || '0.3') || 0.3,
      weightUnit: cols[idx('weightUnit')] || 'kg',
      incoterm: cols[idx('incoterm')] || 'EXW',
      allowLocalPickup: (cols[idx('allowLocalPickup')] || 'false').toLowerCase()==='true',
      deliveryDays: parseInt(cols[idx('deliveryDays')] || '7') || 7,
      country: cols[idx('country')] || 'United States',
      state: cols[idx('state')] || '',
      description: cols[idx('description')] || '',
      keywords: (cols[idx('keywords')] || '').split(/;|,/).filter(Boolean),
      photos: [],
      photoUrls: [],
      acceptedPayments: ['PayPal'],
      autoShareLinkedIn: false,
      autoShareTwitter: false,
      selectedPlatforms: [],
      platformStatuses: {},
      privateNotes: '',
      manufacturerType: 'not_specified',
    }))
    setItems([...items, ...newItems])
    alert(`${newItems.length} item(s) added from CSV`)
  }

  // Quick import by dropping onto the bulk upload area
  const quickImportCsv = async (file: File) => {
    const text = await file.text()
    const { headers, rows } = parseCsvText(text)
    const missing = requiredHeaders.filter(h => !headers.includes(h))
    if (missing.length) {
      alert(`Missing required headers: ${missing.join(', ')}`)
      return
    }
    const idx = (h: string) => headers.indexOf(h)
    const newItems: ComprehensiveListingItem[] = rows.map((cols) => ({
      id: `${Date.now()}-${Math.random().toString(36).slice(2,8)}`,
      productType: (cols[idx('productType')] as any) || 'phone',
      category: cols[idx('category')] || '',
      brand: cols[idx('brand')] || '',
      productName: cols[idx('productName')] || '',
      modelCode: cols[idx('modelCode')] || '',
      condition: cols[idx('condition')] || 'New',
      customCondition: '',
      conditionGrade: 'A',
      lcdDefects: 'None',
      qualityCertification: '',
      memory: cols[idx('memory')] || '128GB',
      color: cols[idx('color')] || 'Black',
      marketSpec: cols[idx('marketSpec')] || 'US',
      simLockStatus: cols[idx('simLockStatus')] || 'Unlocked',
      carrier: cols[idx('carrier')] || '',
      price: parseFloat(cols[idx('price')] || '0') || 0,
      currency: cols[idx('currency')] || 'USD',
      quantity: parseInt(cols[idx('quantity')] || '1') || 1,
      minimumOrderQuantity: parseInt(cols[idx('minimumOrderQuantity')] || '1') || 1,
      supplyAbility: cols[idx('supplyAbility')] || '',
      packaging: cols[idx('packaging')] || 'Original Box',
      itemWeight: parseFloat(cols[idx('itemWeight')] || '0.3') || 0.3,
      weightUnit: cols[idx('weightUnit')] || 'kg',
      incoterm: cols[idx('incoterm')] || 'EXW',
      allowLocalPickup: (cols[idx('allowLocalPickup')] || 'false').toLowerCase()==='true',
      deliveryDays: parseInt(cols[idx('deliveryDays')] || '7') || 7,
      country: cols[idx('country')] || 'United States',
      state: cols[idx('state')] || '',
      description: cols[idx('description')] || '',
      keywords: (cols[idx('keywords')] || '').split(/;|,/).filter(Boolean),
      photos: [],
      photoUrls: [],
      acceptedPayments: ['PayPal'],
      autoShareLinkedIn: false,
      autoShareTwitter: false,
      selectedPlatforms: [],
      platformStatuses: {},
      privateNotes: '',
      manufacturerType: 'not_specified',
    }))
    setItems([...items, ...newItems])
    alert(`${newItems.length} item(s) added from CSV`)
  }

  const handleSheetUpload = async (file: File) => {
    const text = await file.text()
    const lines = text.split(/\r?\n/).filter(Boolean)
    if (lines.length < 2) return
    const headers = lines[0].split(',').map(h=>h.trim())
    const required = ['productType','category','brand','productName','modelCode','condition','price','currency','quantity','country']
    const hasAll = required.every(h=>headers.includes(h))
    if (!hasAll) {
      alert(`Missing required headers. Required: ${required.join(', ')}`)
      return
    }
    const idx = (h:string)=>headers.indexOf(h)
    const newItems: ComprehensiveListingItem[] = lines.slice(1).map((line)=>{
      const cols = line.split(',')
      return {
        id: `${Date.now()}-${Math.random().toString(36).slice(2,8)}`,
        productType: (cols[idx('productType')] as any) || 'phone',
        category: cols[idx('category')] || '',
        brand: cols[idx('brand')] || '',
        productName: cols[idx('productName')] || '',
        modelCode: cols[idx('modelCode')] || '',
        condition: cols[idx('condition')] || 'New',
        customCondition: '',
        conditionGrade: 'A',
        lcdDefects: 'None',
        qualityCertification: '',
        memory: cols[idx('memory')] || '128GB',
        color: cols[idx('color')] || 'Black',
        marketSpec: cols[idx('marketSpec')] || 'US',
        simLockStatus: cols[idx('simLockStatus')] || 'Unlocked',
        carrier: cols[idx('carrier')] || '',
        price: parseFloat(cols[idx('price')] || '0') || 0,
        currency: cols[idx('currency')] || 'USD',
        quantity: parseInt(cols[idx('quantity')] || '1') || 1,
        minimumOrderQuantity: parseInt(cols[idx('minimumOrderQuantity')] || '1') || 1,
        supplyAbility: cols[idx('supplyAbility')] || '',
        packaging: cols[idx('packaging')] || 'Original Box',
        itemWeight: parseFloat(cols[idx('itemWeight')] || '0.3') || 0.3,
        weightUnit: cols[idx('weightUnit')] || 'kg',
        incoterm: cols[idx('incoterm')] || 'EXW',
        allowLocalPickup: (cols[idx('allowLocalPickup')] || 'false').toLowerCase()==='true',
        deliveryDays: parseInt(cols[idx('deliveryDays')] || '7') || 7,
        country: cols[idx('country')] || 'United States',
        state: cols[idx('state')] || '',
        description: cols[idx('description')] || '',
        keywords: (cols[idx('keywords')] || '').split(/;|,/).filter(Boolean),
        photos: [],
        photoUrls: [],
        acceptedPayments: ['PayPal'],
        autoShareLinkedIn: false,
        autoShareTwitter: false,
        selectedPlatforms: [],
        platformStatuses: {},
        privateNotes: '',
        manufacturerType: 'not_specified',
      }
    })
    setItems([...items, ...newItems])
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Phone catalog provided via PHONE_CATALOG import */}
      {/* Gmail Connect Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Gmail Connection</CardTitle>
          <CardDescription>Authenticate to fetch 2FA verification codes automatically</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <Badge variant={gmailStatus === "authenticated" ? "default" : gmailStatus === "requires_auth" ? "destructive" : "secondary"}>
              {gmailStatus === "authenticated" ? "Authenticated" : gmailStatus === "requires_auth" ? "Authentication required" : "Not configured"}
            </Badge>
            <Button size="sm" asChild>
              <a href={`${API_BASE_URL}/gmail/auth?redirect=true`}>Connect Google</a>
            </Button>
            <Button size="sm" variant="outline" onClick={fetchGmailRefreshToken}>Check Token</Button>
          </div>
          {gmailRefreshToken && (
            <div className="flex items-center gap-2">
              <Input value={gmailRefreshToken} readOnly className="font-mono" />
              <Button size="sm" onClick={() => navigator.clipboard.writeText(gmailRefreshToken)}>Copy</Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Multi-Platform Listing Bot</CardTitle>
          <CardDescription>
            Create comprehensive listings with AI-powered enrichment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Bulk Upload Modal Launcher */}
          <div className="flex justify-between items-center p-4 border rounded-md">
            <DragDropCsv onFile={(f)=>quickImportCsv(f)}>
              <div className="flex-1">
                <h4 className="font-semibold">Bulk upload</h4>
                <p className="text-sm text-muted-foreground">Drag & drop CSV here or use the button</p>
              </div>
            </DragDropCsv>
            <Dialog>
              <DialogTrigger asChild>
                <Button size="sm">Bulk Upload</Button>
              </DialogTrigger>
              <DialogContent className="max-w-[900px] p-0">
                <div className="max-h-[80vh] overflow-y-auto p-6">
                <DialogHeader>
                  <DialogTitle>Bulk upload from sheet</DialogTitle>
                  <DialogDescription>Use the template and keep the header order. Preview appears below before importing.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="text-sm">
                    <p className="mb-2 font-medium">Required headers (in order):</p>
                    <div className="overflow-x-auto max-h-56 overflow-y-auto rounded border">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="bg-muted">
                            <th className="p-2 text-left">#</th>
                            <th className="p-2 text-left">Header</th>
                            <th className="p-2 text-left">Notes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[
                            ['productType','phone | accessory | gadget'],
                            ['category','e.g. Smartphones'],
                            ['brand','e.g. Apple'],
                            ['productName','e.g. iPhone 14 Pro'],
                            ['modelCode','e.g. A2890'],
                            ['condition','New | Used | Refurbished | Damaged | 14-Days'],
                            ['memory','Optional, e.g. 256GB'],
                            ['color','Optional, e.g. Black'],
                            ['marketSpec','US | Euro | UK | Asia | Arabic | Other'],
                            ['simLockStatus','Unlocked | Locked'],
                            ['carrier','Optional'],
                            ['price','Number'],
                            ['currency','USD | EUR | GBP'],
                            ['quantity','Number'],
                            ['minimumOrderQuantity','Number'],
                            ['supplyAbility','Optional'],
                            ['packaging','Original Box | Bulk Packed ...'],
                            ['itemWeight','Number, e.g. 0.3'],
                            ['weightUnit','kg | lbs'],
                            ['incoterm','EXW | FOB | ...'],
                            ['allowLocalPickup','true | false'],
                            ['deliveryDays','Number'],
                            ['country','e.g. United States'],
                            ['state','Optional'],
                            ['description','Optional'],
                            ['keywords','Optional; semicolon or comma separated']
                          ].map((row, i) => (
                            <tr key={i} className={i % 2 ? 'bg-background' : ''}>
                              <td className="p-2 align-top border-t">{i + 1}</td>
                              <td className="p-2 align-top border-t font-mono">{row[0]}</td>
                              <td className="p-2 align-top border-t text-muted-foreground">{row[1]}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div className="flex gap-3 items-center">
                    <input type="file" accept=".csv" onChange={(e)=>{ const f=e.target.files?.[0]; if (f) handleCsvFile(f) }} />
                    <Button variant="outline" onClick={downloadExampleSheet}>Download example CSV</Button>
                    <Button onClick={createItemsFromPreview} disabled={!csvPreview.rows.length || !!csvErrors.length}>Import rows</Button>
                  </div>
                  {!!csvErrors.length && (
                    <div className="text-sm text-destructive">{csvErrors[0]}</div>
                  )}
                  {csvPreview.rows.length > 0 && (
                    <div className="max-h-64 overflow-auto border rounded">
                      <table className="w-full text-xs">
                        <thead className="sticky top-0 bg-muted">
                          <tr>
                            {csvPreview.headers.map((h, i) => (
                              <th key={i} className="p-2 text-left border-b font-mono">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {csvPreview.rows.slice(0, 200).map((r, i) => (
                            <tr key={i} className={i % 2 ? 'bg-background' : ''}>
                              {r.map((c, j) => (
                                <td key={j} className="p-2 border-b whitespace-nowrap">{c}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
                </div>
                <DialogFooter className="p-4 border-t">
                  <span className="text-xs text-muted-foreground">Tip: Export your Google Sheet as CSV (File → Download → Comma-separated values)</span>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {items.map((item, index) => (
            <Card key={item.id} className="p-6 space-y-6">
              <div className="flex justify-between items-center gap-3 flex-wrap">
                <h3 className="text-lg font-semibold">Item {index + 1}</h3>
                <div className="flex items-center gap-3 flex-wrap">
                  <Label className="text-sm text-muted-foreground">Post to Platforms</Label>
                  <Badge variant="secondary">{item.selectedPlatforms.length} selected</Badge>
                  {[
                    "hubx",
                    "gsmexchange",
                    "kardof",
                    "cellpex",
                    "handlot",
                  ].map((platform) => (
                    <div key={platform} className="flex items-center space-x-2">
                      <Checkbox
                        checked={item.selectedPlatforms.includes(platform)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            updateItem(item.id, {
                              selectedPlatforms: [...item.selectedPlatforms, platform],
                            })
                          } else {
                            updateItem(item.id, {
                              selectedPlatforms: item.selectedPlatforms.filter((p) => p !== platform),
                            })
                          }
                        }}
                      />
                      <Label className="capitalize text-sm">{platform}</Label>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fillExampleData(item.id)}
                  >
                    <Upload className="h-4 w-4 mr-1" />
                    Fill Example
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeItem(item.id)}
                  >
                    <X className="h-4 w-4" />
                    Remove
                  </Button>
                </div>
              </div>

              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="basic">Basic Info</TabsTrigger>
                  <TabsTrigger value="specs">Specs & Condition</TabsTrigger>
                  <TabsTrigger value="pricing">Pricing & Shipping</TabsTrigger>
                  <TabsTrigger value="media">Media & Description</TabsTrigger>
                </TabsList>

                <TabsContent value="basic" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* Product Type (prominent three-selector) */}
                    <div className="space-y-2">
                      <Label>Category</Label>
                      <ToggleGroup
                        type="single"
                        value={item.productType}
                        onValueChange={(value) => {
                          if (!value) return
                          updateItem(item.id, {
                            productType: value as any,
                            category: value === "phone" ? "Smartphones" : value === "accessory" ? "Antennas" : "Gadgets"
                          })
                        }}
                        className="flex gap-2"
                      >
                        <ToggleGroupItem value="phone" aria-label="Smartphones">Smartphones</ToggleGroupItem>
                        <ToggleGroupItem value="accessory" aria-label="Accessories">Accessories</ToggleGroupItem>
                        <ToggleGroupItem value="gadget" aria-label="Gadgets">Gadgets</ToggleGroupItem>
                      </ToggleGroup>
                    </div>

                    {/* Removed inline platforms here; moved to header */}

                    {/* Category */}
                    <div className="space-y-2">
                      <Label>Category</Label>
                      <Select
                        value={item.category}
                        onValueChange={(value) => updateItem(item.id, { category: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          {CATEGORIES[item.productType === "phone" ? "phones" : item.productType === "accessory" ? "accessories" : "gadgets"].map((cat) => (
                            <SelectItem key={cat} value={cat}>
                              {cat}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Brand */}
                    <div className="space-y-2">
                      <Label>Brand</Label>
                      <Input
                        value={item.brand}
                        onChange={(e) => updateItem(item.id, { brand: e.target.value })}
                        placeholder="e.g., Apple, Samsung"
                      />
                    </div>

                    {/* Product Name with focus/blur-controlled autocomplete (model-only) */}
                    <div className="space-y-2">
                      <Label>Product Name</Label>
                      <div className="relative">
                        <Input
                          value={item.productName}
                          onChange={(e) => updateItem(item.id, { productName: e.target.value })}
                          placeholder="e.g., iPhone 14 Pro"
                          autoComplete="off"
                          onFocus={() => setActiveSuggestItemId(item.id)}
                          onBlur={() => setActiveSuggestItemId((curr) => (curr === item.id ? null : curr))}
                        />
                        {activeSuggestItemId === item.id && phoneCatalog.length > 0 && (
                          <div className="absolute z-10 mt-1 w-full max-h-52 overflow-auto rounded-md border bg-popover text-popover-foreground shadow">
                            {(() => {
                              const q = (item.productName || "").toLowerCase()
                              const brandFilter = (item.brand || "").toLowerCase()
                              const matches = phoneCatalog.filter((p) => {
                                const brandOk = brandFilter ? p.brand.toLowerCase() === brandFilter : true
                                const qOk = q ? (p.model.toLowerCase().includes(q) || p.label.toLowerCase().includes(q)) : true
                                return brandOk && qOk
                              }).slice(0, 20)
                              return matches.map((p) => (
                                <div
                                  key={p.label}
                                  className="px-3 py-2 cursor-pointer hover:bg-accent"
                                  onMouseDown={(e) => {
                                    e.preventDefault()
                                    // Set model only; brand stays separate
                                    updateItem(item.id, { productName: p.model, brand: item.brand || p.brand })
                                    setActiveSuggestItemId(null)
                                  }}
                                >
                                  {p.model}
                                  <span className="ml-2 text-xs text-muted-foreground">{p.brand}</span>
                                </div>
                              ))
                            })()}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Model Code */}
                    <div className="space-y-2">
                      <Label>Model/Code</Label>
                      <Input
                        value={item.modelCode}
                        onChange={(e) => updateItem(item.id, { modelCode: e.target.value })}
                        placeholder="e.g., A2890"
                      />
                    </div>

                    {/* Manufacturer Type */}
                    <div className="space-y-2">
                      <Label>Manufacturer Type</Label>
                      <Select
                        value={item.manufacturerType}
                        onValueChange={(value: "OEM" | "ODM" | "not_specified") => 
                          updateItem(item.id, { manufacturerType: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="not_specified">Not specified</SelectItem>
                          <SelectItem value="OEM">OEM</SelectItem>
                          <SelectItem value="ODM">ODM</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="specs" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* Condition */}
                    <div className="space-y-2">
                      <Label>Condition</Label>
                      {item.condition === "other" ? (
                        <div className="space-y-2">
                          <Input
                            value={item.customCondition}
                            onChange={(e) => updateItem(item.id, { customCondition: e.target.value })}
                            placeholder="Enter custom condition"
                            autoFocus
                          />
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => updateItem(item.id, { condition: "New", customCondition: "" })}
                          >
                            Back to dropdown
                          </Button>
                        </div>
                      ) : (
                        <Select
                          value={item.condition}
                          onValueChange={(value) => {
                            if (value === "other") {
                              updateItem(item.id, { condition: "other" })
                            } else {
                              updateItem(item.id, { condition: value, customCondition: "" })
                            }
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {CONDITIONS.map((condition) => (
                              <SelectItem key={condition} value={condition}>
                                {condition}
                              </SelectItem>
                            ))}
                            <SelectItem value="other">Other (Custom)</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    </div>

                    {/* Condition Grade (phones only) */}
                    {item.productType === "phone" && (
                      <div className="space-y-2">
                        <Label>Grade</Label>
                        <Select
                          value={item.conditionGrade}
                          onValueChange={(value) => updateItem(item.id, { conditionGrade: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {CONDITION_GRADES.map((grade) => (
                              <SelectItem key={grade} value={grade}>
                                Grade {grade}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* LCD Defects (phones only) */}
                    {item.productType === "phone" && (
                      <div className="space-y-2">
                        <Label>LCD Defects</Label>
                        <Select
                          value={item.lcdDefects}
                          onValueChange={(value) => updateItem(item.id, { lcdDefects: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {LCD_DEFECTS.map((defect) => (
                              <SelectItem key={defect} value={defect}>
                                {defect}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* Memory (phones only) */}
                    {item.productType === "phone" && (
                      <div className="space-y-2">
                        <Label>Memory/Storage</Label>
                        <Select
                          value={item.memory}
                          onValueChange={(value) => updateItem(item.id, { memory: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {MEMORY_OPTIONS.map((memory) => (
                              <SelectItem key={memory} value={memory}>
                                {memory}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* Color (phones only) */}
                    {item.productType === "phone" && (
                      <div className="space-y-2">
                        <Label>Color</Label>
                        <Select
                          value={item.color}
                          onValueChange={(value) => updateItem(item.id, { color: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {COLORS.map((color) => (
                              <SelectItem key={color} value={color}>
                                {color}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* Market Spec (phones only) */}
                    {item.productType === "phone" && (
                      <div className="space-y-2">
                        <Label>Market Spec</Label>
                        <Select
                          value={item.marketSpec}
                          onValueChange={(value) => updateItem(item.id, { marketSpec: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {MARKET_SPECS.map((spec) => (
                              <SelectItem key={spec} value={spec}>
                                {spec}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* SIM Lock Status (phones only) */}
                    {item.productType === "phone" && (
                      <div className="space-y-2">
                        <Label>SIM Lock Status</Label>
                        <Select
                          value={item.simLockStatus}
                          onValueChange={(value) => updateItem(item.id, { simLockStatus: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {SIM_LOCK_STATUS.map((status) => (
                              <SelectItem key={status} value={status}>
                                {status}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* Carrier (phones only) */}
                    {item.productType === "phone" && (
                      <div className="space-y-2">
                        <Label>Carrier</Label>
                        <Input
                          value={item.carrier}
                          onChange={(e) => updateItem(item.id, { carrier: e.target.value })}
                          placeholder="e.g., AT&T, Verizon"
                        />
                      </div>
                    )}

                    {/* Quality Certification */}
                    <div className="space-y-2">
                      <Label>Quality/Safety Certification</Label>
                      <Input
                        value={item.qualityCertification}
                        onChange={(e) => updateItem(item.id, { qualityCertification: e.target.value })}
                        placeholder="e.g., CE, FCC"
                      />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="pricing" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* Price and Currency */}
                    <div className="space-y-2">
                      <Label>Price</Label>
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          value={item.price}
                          onChange={(e) => updateItem(item.id, { price: parseFloat(e.target.value) || 0 })}
                          placeholder="0.00"
                        />
                        <Select
                          value={item.currency}
                          onValueChange={(value) => updateItem(item.id, { currency: value })}
                        >
                          <SelectTrigger className="w-24">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {CURRENCIES.map((curr) => (
                              <SelectItem key={curr} value={curr}>
                                {curr}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Quantity */}
                    <div className="space-y-2">
                      <Label>Quantity</Label>
                      <div className="flex items-center gap-2">
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => updateItem(item.id, { 
                            quantity: Math.max(1, item.quantity - 1) 
                          })}
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        <Input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => updateItem(item.id, { 
                            quantity: parseInt(e.target.value) || 1 
                          })}
                          className="w-20 text-center"
                        />
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => updateItem(item.id, { 
                            quantity: item.quantity + 1 
                          })}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Minimum Order Quantity */}
                    <div className="space-y-2">
                      <Label>Minimum Order Quantity</Label>
                      <Input
                        type="number"
                        value={item.minimumOrderQuantity}
                        onChange={(e) => updateItem(item.id, { 
                          minimumOrderQuantity: parseInt(e.target.value) || 1 
                        })}
                      />
                    </div>

                    {/* Supply Ability */}
                    <div className="space-y-2">
                      <Label>Supply Ability</Label>
                      <Input
                        value={item.supplyAbility}
                        onChange={(e) => updateItem(item.id, { supplyAbility: e.target.value })}
                        placeholder="e.g., 1000 units/month"
                      />
                    </div>

                    {/* Packaging */}
                    <div className="space-y-2">
                      <Label>Packaging</Label>
                      <Select
                        value={item.packaging}
                        onValueChange={(value) => updateItem(item.id, { packaging: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PACKAGING_OPTIONS.map((pack) => (
                            <SelectItem key={pack} value={pack}>
                              {pack}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Item Weight */}
                    <div className="space-y-2">
                      <Label>Item Weight</Label>
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          step="0.1"
                          value={item.itemWeight}
                          onChange={(e) => updateItem(item.id, { 
                            itemWeight: parseFloat(e.target.value) || 0 
                          })}
                        />
                        <Select
                          value={item.weightUnit}
                          onValueChange={(value) => updateItem(item.id, { weightUnit: value })}
                        >
                          <SelectTrigger className="w-20">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {WEIGHT_UNITS.map((unit) => (
                              <SelectItem key={unit} value={unit}>
                                {unit}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Incoterm */}
                    <div className="space-y-2">
                      <Label>Incoterm</Label>
                      <Select
                        value={item.incoterm}
                        onValueChange={(value) => updateItem(item.id, { incoterm: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {INCOTERMS.map((term) => (
                            <SelectItem key={term} value={term}>
                              {term}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Delivery Days */}
                    <div className="space-y-2">
                      <Label>Delivery Time (days)</Label>
                      <Input
                        type="number"
                        value={item.deliveryDays}
                        onChange={(e) => updateItem(item.id, { 
                          deliveryDays: parseInt(e.target.value) || 7 
                        })}
                      />
                    </div>

                    {/* Country */}
                    <div className="space-y-2">
                      <Label>Country</Label>
                      <Input
                        value={item.country}
                        onChange={(e) => updateItem(item.id, { country: e.target.value })}
                      />
                    </div>

                    {/* State */}
                    <div className="space-y-2">
                      <Label>State/Province</Label>
                      <Input
                        value={item.state}
                        onChange={(e) => updateItem(item.id, { state: e.target.value })}
                        placeholder="e.g., Florida"
                      />
                    </div>

                    {/* Local Pickup */}
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        checked={item.allowLocalPickup}
                        onCheckedChange={(checked) => 
                          updateItem(item.id, { allowLocalPickup: checked as boolean })
                        }
                      />
                      <Label>Allow local pickup</Label>
                    </div>

                    {/* Accepted Payments */}
                    <div className="space-y-2">
                      <Label>Accepted Payments</Label>
                      <div className="space-y-2">
                        {PAYMENT_METHODS.map((method) => (
                          <div key={method} className="flex items-center space-x-2">
                            <Checkbox
                              checked={item.acceptedPayments.includes(method)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  updateItem(item.id, {
                                    acceptedPayments: [...item.acceptedPayments, method]
                                  })
                                } else {
                                  updateItem(item.id, {
                                    acceptedPayments: item.acceptedPayments.filter(m => m !== method)
                                  })
                                }
                              }}
                            />
                            <Label>{method}</Label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="media" className="space-y-4">
                  {/* Photo Upload */}
                  <div className="space-y-2">
                    <Label>Product Photos</Label>
                    <div className="border-2 border-dashed rounded-lg p-4">
                      <input
                        type="file"
                        multiple
                        accept="image/*"
                        onChange={(e) => e.target.files && handlePhotoUpload(item.id, e.target.files)}
                        className="hidden"
                        id={`photo-upload-${item.id}`}
                      />
                      <label
                        htmlFor={`photo-upload-${item.id}`}
                        className="flex flex-col items-center cursor-pointer"
                      >
                        <Upload className="h-8 w-8 mb-2 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          Click to upload photos or drag and drop
                        </span>
                      </label>
                    </div>
                    {item.photoUrls.length > 0 && (
                      <div className="flex gap-2 mt-2 flex-wrap">
                        {item.photoUrls.map((url, idx) => (
                          <div key={idx} className="relative">
                            <img
                              src={url}
                              alt={`Product ${idx + 1}`}
                              className="w-20 h-20 object-cover rounded"
                            />
                            <button
                              onClick={() => {
                                const newPhotos = item.photos.filter((_, i) => i !== idx)
                                const newUrls = item.photoUrls.filter((_, i) => i !== idx)
                                updateItem(item.id, { photos: newPhotos, photoUrls: newUrls })
                              }}
                              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Description */}
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={item.description}
                      onChange={(e) => updateItem(item.id, { description: e.target.value })}
                      placeholder="AI will generate this from photos, or enter manually..."
                      rows={4}
                    />
                  </div>

                  {/* Keywords */}
                  <div className="space-y-2">
                    <Label>Keywords</Label>
                    <Input
                      value={item.keywords.join(", ")}
                      onChange={(e) => updateItem(item.id, { 
                        keywords: e.target.value.split(",").map(k => k.trim()).filter(Boolean)
                      })}
                      placeholder="AI will generate, or enter comma-separated keywords"
                    />
                  </div>

                  {/* Private Notes */}
                  <div className="space-y-2">
                    <Label>Private Notes</Label>
                    <Textarea
                      value={item.privateNotes}
                      onChange={(e) => updateItem(item.id, { privateNotes: e.target.value })}
                      placeholder="Internal notes (not published)"
                      rows={3}
                    />
                  </div>

                  {/* Auto-share Options */}
                  <div className="space-y-2">
                    <Label>Auto-share on social media</Label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={item.autoShareLinkedIn}
                          onCheckedChange={(checked) => 
                            updateItem(item.id, { autoShareLinkedIn: checked as boolean })
                          }
                        />
                        <Label>LinkedIn</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={item.autoShareTwitter}
                          onCheckedChange={(checked) => 
                            updateItem(item.id, { autoShareTwitter: checked as boolean })
                          }
                        />
                        <Label>Twitter</Label>
                      </div>
                    </div>
                  </div>
                </TabsContent>

                {/* Remove old Platforms tab content */}
                {/* (deleted) */}
              </Tabs>
            </Card>
          ))}

          <Button
            onClick={addNewItem}
            variant="outline"
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add New Item
          </Button>

          <Button
            onClick={() => items.forEach(item => fillExampleData(item.id))}
            variant="outline"
            className="w-full"
          >
            <Upload className="h-4 w-4 mr-2" />
            Fill Example Data for All Items
          </Button>

          <Button
            onClick={submitForProcessing}
            disabled={isProcessing || items.length === 0}
            className="w-full"
          >
            {isProcessing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              "Submit for Processing"
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
