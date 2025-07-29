"use client"

import { useState, useEffect } from "react"
import { Plus, Minus, X, Check, Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { Badge } from "@/components/ui/badge"

const API_BASE_URL = "https://listing-bot-api-production.up.railway.app"

const PLATFORMS = [
  { id: "hubx", name: "HubX", color: "bg-blue-500" },
  { id: "gsmexchange", name: "GSM Exchange", color: "bg-green-500" },
  { id: "kardof", name: "Kardof", color: "bg-purple-500" },
  { id: "cellpex", name: "Cellpex", color: "bg-orange-500" },
  { id: "handlot", name: "Handlot", color: "bg-pink-500" },
]

const CONDITIONS = [
  "New",
  "Like New",
  "Used - Excellent",
  "Used - Good",
  "Used - Fair",
  "Refurbished",
  "For Parts",
]

type PlatformStatus = "pending" | "posting" | "success" | "error"

type ListingItem = {
  id: string
  productName: string
  condition: string
  customCondition: string
  quantity: number
  price: number
  selectedPlatforms: string[]
  platformStatuses: Record<string, { status: PlatformStatus; message?: string }>
}

export default function ListingBotPage() {
  const [items, setItems] = useState<ListingItem[]>([])
  const [productSuggestions, setProductSuggestions] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const { toast } = useToast()

  // Load product suggestions from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("productHistory")
    if (saved) {
      setProductSuggestions(JSON.parse(saved))
    }
  }, [])

  const addNewItem = () => {
    const newItem: ListingItem = {
      id: Date.now().toString(),
      productName: "",
      condition: "New",
      customCondition: "",
      quantity: 1,
      price: 0,
      selectedPlatforms: [],
      platformStatuses: {},
    }
    setItems([...items, newItem])
  }

  const updateItem = (id: string, updates: Partial<ListingItem>) => {
    setItems(items.map(item => item.id === id ? { ...item, ...updates } : item))
  }

  const removeItem = (id: string) => {
    setItems(items.filter(item => item.id !== id))
  }

  const togglePlatform = (itemId: string, platformId: string) => {
    const item = items.find(i => i.id === itemId)
    if (!item) return

    const platforms = item.selectedPlatforms.includes(platformId)
      ? item.selectedPlatforms.filter(p => p !== platformId)
      : [...item.selectedPlatforms, platformId]

    updateItem(itemId, { selectedPlatforms: platforms })
  }

  const updateQuantity = (id: string, delta: number) => {
    const item = items.find(i => i.id === id)
    if (item) {
      const newQty = Math.max(1, item.quantity + delta)
      updateItem(id, { quantity: newQty })
    }
  }

  const updatePrice = (id: string, delta: number) => {
    const item = items.find(i => i.id === id)
    if (item) {
      const newPrice = Math.max(0, item.price + delta)
      updateItem(id, { price: newPrice })
    }
  }

  const saveProductName = (name: string) => {
    if (name && !productSuggestions.includes(name)) {
      const updated = [...productSuggestions, name]
      setProductSuggestions(updated)
      localStorage.setItem("productHistory", JSON.stringify(updated))
    }
  }

  const submitForProcessing = async () => {
    // Validate items
    const validItems = items.filter(item => 
      item.productName && item.selectedPlatforms.length > 0 && item.price > 0
    )

    if (validItems.length === 0) {
      toast({
        variant: "destructive",
        title: "No valid items",
        description: "Please add at least one item with a name, price, and selected platforms.",
      })
      return
    }

    setIsProcessing(true)

    // Save product names
    validItems.forEach(item => saveProductName(item.productName))

    // Process each item for each platform
    for (const item of validItems) {
      // Initialize all platform statuses to pending
      const statuses: Record<string, { status: PlatformStatus; message?: string }> = {}
      item.selectedPlatforms.forEach(platform => {
        statuses[platform] = { status: "pending" }
      })
      updateItem(item.id, { platformStatuses: statuses })

      // Process each platform for this item
      for (const platformId of item.selectedPlatforms) {
        // Update status to posting
        updateItem(item.id, {
          platformStatuses: {
            ...item.platformStatuses,
            [platformId]: { status: "posting" }
          }
        })

                  try {
            // Call API to post this item to this platform
            const response = await fetch(`${API_BASE_URL}/listings/single`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                platform: platformId,
                product_name: item.productName,
                condition: item.condition === "other" ? item.customCondition : item.condition,
                quantity: item.quantity,
                price: item.price,
              }),
            })

          const result = await response.json()

          if (response.ok) {
            updateItem(item.id, {
              platformStatuses: {
                ...item.platformStatuses,
                [platformId]: { status: "success", message: "Posted successfully" }
              }
            })
          } else {
            updateItem(item.id, {
              platformStatuses: {
                ...item.platformStatuses,
                [platformId]: { status: "error", message: result.message || "Failed to post" }
              }
            })
          }
        } catch (error) {
          updateItem(item.id, {
            platformStatuses: {
              ...item.platformStatuses,
              [platformId]: { status: "error", message: "Network error" }
            }
          })
        }

        // Small delay between platform postings
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }

    setIsProcessing(false)
    toast({
      title: "Processing complete",
      description: "Check the status of each listing below.",
    })
  }

  return (
    <div className="bg-slate-50 min-h-screen w-full">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-slate-800">Multi-Platform Listing Bot</h1>
        </div>
      </header>
      
      <main className="container mx-auto p-4 sm:p-6 lg:p-8">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Add Items Section */}
          <Card>
            <CardHeader>
              <CardTitle>Your Listings</CardTitle>
              <CardDescription>
                Add items and select which platforms to post them on
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {items.map((item) => (
                <Card key={item.id} className="p-4">
                  <div className="space-y-4">
                    {/* Product Name */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Product Name</Label>
                        <Input
                          value={item.productName}
                          onChange={(e) => updateItem(item.id, { productName: e.target.value })}
                          placeholder="e.g. iPhone 14 Pro"
                          list={`suggestions-${item.id}`}
                        />
                        <datalist id={`suggestions-${item.id}`}>
                          {productSuggestions.map((suggestion) => (
                            <option key={suggestion} value={suggestion} />
                          ))}
                        </datalist>
                      </div>

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
                    </div>

                    {/* Quantity and Price */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Quantity</Label>
                        <div className="flex items-center gap-2">
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => updateQuantity(item.id, -1)}
                          >
                            <Minus className="h-4 w-4" />
                          </Button>
                          <Input
                            type="number"
                            value={item.quantity}
                            onChange={(e) => updateItem(item.id, { quantity: parseInt(e.target.value) || 0 })}
                            className="w-20 text-center"
                          />
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => updateQuantity(item.id, 1)}
                          >
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Price ($)</Label>
                        <div className="flex items-center gap-2">
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => updatePrice(item.id, -10)}
                          >
                            <Minus className="h-4 w-4" />
                          </Button>
                          <Input
                            type="number"
                            value={item.price}
                            onChange={(e) => updateItem(item.id, { price: parseFloat(e.target.value) || 0 })}
                            className="w-24 text-center"
                          />
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => updatePrice(item.id, 10)}
                          >
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Platform Selection */}
                    <div className="space-y-2">
                      <Label>Select Platforms</Label>
                      <div className="flex flex-wrap gap-3">
                        {PLATFORMS.map((platform) => (
                          <label
                            key={platform.id}
                            className="flex items-center gap-2 cursor-pointer"
                          >
                            <Checkbox
                              checked={item.selectedPlatforms.includes(platform.id)}
                              onCheckedChange={() => togglePlatform(item.id, platform.id)}
                            />
                            <span className="text-sm">{platform.name}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Platform Status */}
                    {Object.keys(item.platformStatuses).length > 0 && (
                      <div className="space-y-2">
                        <Label>Status</Label>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(item.platformStatuses).map(([platform, status]) => {
                            const platformInfo = PLATFORMS.find(p => p.id === platform)
                            return (
                              <Badge
                                key={platform}
                                variant={status.status === "success" ? "default" : status.status === "error" ? "destructive" : "secondary"}
                                className="flex items-center gap-1"
                              >
                                {status.status === "posting" && <Loader2 className="h-3 w-3 animate-spin" />}
                                {status.status === "success" && <Check className="h-3 w-3" />}
                                {status.status === "error" && <AlertCircle className="h-3 w-3" />}
                                {platformInfo?.name}
                                {status.message && `: ${status.message}`}
                              </Badge>
                            )
                          })}
                        </div>
                      </div>
                    )}

                    {/* Remove Item Button */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeItem(item.id)}
                      className="text-red-600"
                    >
                      <X className="h-4 w-4 mr-1" />
                      Remove
                    </Button>
                  </div>
                </Card>
              ))}

              {/* Add New Item Button */}
              <Button onClick={addNewItem} variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add New Item
              </Button>
            </CardContent>
          </Card>

          {/* Submit Button */}
          <Button
            onClick={submitForProcessing}
            disabled={items.length === 0 || isProcessing}
            className="w-full"
            size="lg"
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              "Submit for Processing"
            )}
          </Button>
        </div>
      </main>
      <Toaster />
    </div>
  )
}
