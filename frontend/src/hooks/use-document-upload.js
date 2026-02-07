import * as React from 'react'
import api from '@/services/api'
import { useAppStore } from '@/store/useAppStore'
import { useAuth } from '@/auth/AuthProvider'

export function useDocumentUpload() {
    const { isOffline } = useAuth()
    const { setUploadedDocument, uploadedDocument } = useAppStore()

    const [uploading, setUploading] = React.useState(false)
    const [error, setError] = React.useState(null)

    const uploadDocument = React.useCallback(async (file) => {
        if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
            setError('Only PDF files are supported')
            return null
        }

        setUploading(true)
        setError(null)

        // Demo mode mock
        if (isOffline || !api.accessToken) {
            await new Promise(r => setTimeout(r, 1000))
            const mockResult = {
                upload_id: `demo-${Date.now()}`,
                namespace: `demo_ns_${Date.now()}`,
                filename: file.name,
                chunk_count: Math.floor(Math.random() * 10) + 5,
            }
            setUploadedDocument(mockResult)
            setUploading(false)
            return mockResult
        }

        try {
            const result = await api.uploadDocument(file)
            setUploadedDocument(result)
            return result
        } catch (err) {
            setError(err.message || 'Upload failed')
            return null
        } finally {
            setUploading(false)
        }
    }, [isOffline, setUploadedDocument])

    const clearDocument = React.useCallback(() => {
        setUploadedDocument(null)
        setError(null)
    }, [setUploadedDocument])

    return {
        uploadDocument,
        clearDocument,
        uploading,
        error,
        uploadedDocument,
    }
}
