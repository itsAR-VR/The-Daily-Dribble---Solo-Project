"use client"

import { useState, useEffect, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { UploadCloud, File, CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/toaster"

const API_BASE_URL = "https://listing-bot-api-production.up.railway.app/"

type JobStatus = "pending" | "processing" | "completed" | "error"

export default function ListingBotPage() {
  const [file, setFile] = useState<File | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<JobStatus>("pending")
  const [statusMessage, setStatusMessage] = useState<string>("")
  const [isUploading, setIsUploading] = useState<boolean>(false)
  const [isPolling, setIsPolling] = useState<boolean>(false)

  const { toast } = useToast()

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: any[]) => {
      if (fileRejections.length > 0) {
        toast({
          variant: "destructive",
          title: "Invalid File Type",
          description: "Please upload only .xlsx files.",
        })
        return
      }
      setFile(acceptedFiles[0])
    },
    [toast],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxFiles: 1,
  })

  const handleUpload = async () => {
    if (!file) {
      toast({
        variant: "destructive",
        title: "No File Selected",
        description: "Please select an Excel file to upload.",
      })
      return
    }

    setIsUploading(true)
    setJobStatus("pending")
    setStatusMessage("Uploading file...")

    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch(`${API_BASE_URL}/listings`, {
        method: "POST",
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.message || "Failed to start listing job.")
      }

      setJobId(result.job_id)
      setJobStatus(result.status as JobStatus)
      setStatusMessage(result.message)
      toast({
        title: "Upload Successful",
        description: `Job started with ID: ${result.job_id}`,
      })
    } catch (error: any) {
      setJobStatus("error")
      setStatusMessage(error.message || "An unknown error occurred during upload.")
      toast({
        variant: "destructive",
        title: "Upload Failed",
        description: error.message || "Could not submit the file.",
      })
    } finally {
      setIsUploading(false)
    }
  }

  useEffect(() => {
    if (jobId && (jobStatus === "pending" || jobStatus === "processing")) {
      setIsPolling(true)
      const intervalId = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/listings/${jobId}/status`)
          const result = await response.json()

          if (!response.ok) {
            throw new Error(result.message || "Failed to get job status.")
          }

          setJobStatus(result.status as JobStatus)
          setStatusMessage(result.message)

          if (result.status === "completed" || result.status === "error") {
            setIsPolling(false)
            clearInterval(intervalId)
            if (result.status === "completed") {
              toast({
                title: "Processing Complete",
                description: "Your file is ready for download.",
                className: "bg-green-100 dark:bg-green-900",
              })
            }
          }
        } catch (error: any) {
          setJobStatus("error")
          setStatusMessage(error.message || "An unknown error occurred while polling.")
          setIsPolling(false)
          clearInterval(intervalId)
          toast({
            variant: "destructive",
            title: "Polling Error",
            description: "Could not retrieve job status.",
          })
        }
      }, 5000)

      return () => clearInterval(intervalId)
    }
  }, [jobId, jobStatus, toast])

  const handleDownload = async () => {
    if (!jobId) return
    try {
      const response = await fetch(`${API_BASE_URL}/listings/${jobId}`)
      if (!response.ok) {
        throw new Error("Failed to download the file.")
      }
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `processed_${file?.name || "listings.xlsx"}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Download Failed",
        description: error.message,
      })
    }
  }

  const resetState = () => {
    setFile(null)
    setJobId(null)
    setJobStatus("pending")
    setStatusMessage("")
    setIsPolling(false)
  }

  return (
    <div className="bg-slate-50 min-h-screen w-full">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-slate-800">Listing Bot</h1>
        </div>
      </header>
      <main className="container mx-auto p-4 sm:p-6 lg:p-8">
        <div className="max-w-2xl mx-auto grid gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Upload Your Listings</CardTitle>
              <CardDescription>
                Upload your product listings in an Excel (.xlsx) file to start processing.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div
                {...getRootProps()}
                className={`flex flex-col items-center justify-center p-10 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                  isDragActive ? "border-primary bg-primary/10" : "border-slate-300 hover:border-primary/70"
                }`}
              >
                <input {...getInputProps()} />
                <UploadCloud className="w-12 h-12 text-slate-400 mb-4" />
                <p className="text-center text-slate-500">
                  {isDragActive ? "Drop the file here..." : "Drag & drop a .xlsx file here, or click to select"}
                </p>
              </div>
              {file && (
                <div className="flex items-center justify-between p-3 bg-slate-100 rounded-lg border">
                  <div className="flex items-center gap-3">
                    <File className="w-6 h-6 text-primary" />
                    <div>
                      <p className="font-medium text-sm">{file.name}</p>
                      <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(2)} KB</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => setFile(null)}>
                    <XCircle className="w-5 h-5 text-slate-500" />
                  </Button>
                </div>
              )}
              <Button onClick={handleUpload} disabled={!file || isUploading || isPolling} className="w-full">
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  "Submit for Processing"
                )}
              </Button>
            </CardContent>
          </Card>

          {jobId && (
            <Card>
              <CardHeader>
                <CardTitle>Job Status</CardTitle>
                <CardDescription>Tracking job: {jobId}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  {jobStatus === "completed" && <CheckCircle2 className="w-6 h-6 text-green-500" />}
                  {jobStatus === "processing" && <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />}
                  {jobStatus === "error" && <XCircle className="w-6 h-6 text-red-500" />}
                  {(jobStatus === "pending" || isUploading) && (
                    <Loader2 className="w-6 h-6 text-slate-500 animate-spin" />
                  )}
                  <p className="font-medium capitalize">{statusMessage}</p>
                </div>
                {(jobStatus === "processing" || jobStatus === "pending" || isUploading) && (
                  <Progress value={jobStatus === "processing" ? 50 : 10} className="w-full" />
                )}
                {jobStatus === "completed" && (
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button onClick={handleDownload} className="w-full sm:w-auto flex-grow">
                      Download Processed File
                    </Button>
                    <Button onClick={resetState} variant="outline" className="w-full sm:w-auto bg-transparent">
                      Start New Job
                    </Button>
                  </div>
                )}
                {jobStatus === "error" && (
                  <Button onClick={resetState} variant="outline" className="w-full bg-transparent">
                    Try Again
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Sample Excel Format</CardTitle>
              <CardDescription>Ensure your .xlsx file has the following columns in the first sheet.</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="list-disc list-inside space-y-1 text-sm text-slate-600 bg-slate-100 p-4 rounded-md">
                <li>
                  <span className="font-semibold">platform:</span> The marketplace name (e.g., hubx, gsmexchange, kardof, cellpex, handlot, linkedin).
                </li>
                <li>
                  <span className="font-semibold">product_name:</span> The full name of the product.
                </li>
                <li>
                  <span className="font-semibold">condition:</span> Product condition (e.g., New, Used).
                </li>
                <li>
                  <span className="font-semibold">quantity:</span> Number of items available.
                </li>
                <li>
                  <span className="font-semibold">price:</span> The price of the product.
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </main>
      <Toaster />
    </div>
  )
}
