import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState } from "react"

export default function RequisitionCard() {
    const [confirmed, setConfirmed] = useState(false)

    const job_title = props.job_title || ""
    const requisition_id = props.requisition_id || ""
    const business_function = props.business_function || ""
    const department = props.department || ""
    const level = props.level || ""
    const location = props.location || ""

    function handleConfirm() {
        setConfirmed(true)
        sendUserMessage(
            `Confirmed requisition ${requisition_id} for ${job_title}`
        )
    }

    if (confirmed) {
        return (
            <Card className="flex flex-col" style={{ maxWidth: 400 }}>
                <CardContent className="pt-4 pb-4">
                    <div className="flex items-center gap-2">
                        <span style={{ color: "#065f46", fontSize: 14, fontWeight: 600 }}>
                            Confirmed
                        </span>
                        <span style={{ color: "#6b7280", fontSize: 13 }}>
                            {requisition_id} — {job_title}
                        </span>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className="flex flex-col" style={{ maxWidth: 400 }}>
            <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold leading-tight">
                    {job_title}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                <div className="space-y-1" style={{ fontSize: 13, color: "#374151" }}>
                    <div className="flex justify-between">
                        <span style={{ color: "#6b7280" }}>Requisition ID</span>
                        <span style={{ fontWeight: 500 }}>{requisition_id}</span>
                    </div>
                    <div className="flex justify-between">
                        <span style={{ color: "#6b7280" }}>Business Function</span>
                        <span style={{ fontWeight: 500 }}>{business_function}</span>
                    </div>
                    <div className="flex justify-between">
                        <span style={{ color: "#6b7280" }}>Department</span>
                        <span style={{ fontWeight: 500 }}>{department}</span>
                    </div>
                    <div className="flex justify-between">
                        <span style={{ color: "#6b7280" }}>Level</span>
                        <span style={{ fontWeight: 500 }}>{level}</span>
                    </div>
                    {location && (
                        <div className="flex justify-between">
                            <span style={{ color: "#6b7280" }}>Location</span>
                            <span style={{ fontWeight: 500 }}>{location}</span>
                        </div>
                    )}
                </div>
                <Button
                    onClick={handleConfirm}
                    className="font-medium rounded w-full"
                    style={{ backgroundColor: "#6264A7", color: "#fff" }}
                >
                    Confirm Requisition
                </Button>
            </CardContent>
        </Card>
    )
}
