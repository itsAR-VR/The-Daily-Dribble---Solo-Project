"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function ListingBotUI() {
  const [itemCount, setItemCount] = useState(0)

  const addNewItem = () => {
    setItemCount(prev => prev + 1)
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle>Multi-Platform Listing Bot</CardTitle>
          <CardDescription>
            Create comprehensive listings with AI-powered enrichment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center">
            <p>Items created: {itemCount}</p>
            <Button onClick={addNewItem} className="mt-4">
              Add New Item
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
