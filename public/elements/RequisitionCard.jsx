import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState } from "react"

function SingleRequisition({ req, isSelected, onSelect }) {
    const {
        requisition_id = "",
        job_title = "",
        business_function = "",
        department = "",
        level = "",
        location = "",
    } = req

    return (
        <div
            style={{
                padding: "12px 14px",
                border: isSelected ? "2px solid #6264A7" : "1px solid #e5e7eb",
                borderRadius: 8,
                background: isSelected ? "#f0f0fb" : "#fff",
            }}
        >
            <div className="flex items-center justify-between gap-2">
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "#1f2937" }}>
                        {job_title}
                    </div>
                    <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                        {requisition_id} &middot; {department} &middot; {level}
                        {location ? ` \u00b7 ${location}` : ""}
                    </div>
                    <div style={{ fontSize: 12, color: "#6b7280", marginTop: 1 }}>
                        {business_function}
                    </div>
                </div>
                <Button
                    onClick={() => onSelect(req)}
                    className="font-medium rounded flex-shrink-0"
                    style={
                        isSelected
                            ? { backgroundColor: "#464775", color: "#fff", cursor: "default" }
                            : { backgroundColor: "#6264A7", color: "#fff" }
                    }
                    disabled={isSelected}
                    size="sm"
                >
                    {isSelected ? "Selected" : "Select"}
                </Button>
            </div>
        </div>
    )
}

export default function RequisitionCard() {
    const [selectedId, setSelectedId] = useState(null)

    const requisitions = props.requisitions || []

    function handleSelect(req) {
        setSelectedId(req.requisition_id)
        sendUserMessage(
            `Confirmed requisition ${req.requisition_id} for ${req.job_title}`
        )
    }

    if (selectedId) {
        const selected = requisitions.find(r => r.requisition_id === selectedId)
        return (
            <Card className="flex flex-col" style={{ maxWidth: 480 }}>
                <CardContent className="pt-4 pb-4">
                    <div className="flex items-center gap-2">
                        <span style={{ color: "#065f46", fontSize: 14, fontWeight: 600 }}>
                            Confirmed
                        </span>
                        <span style={{ color: "#6b7280", fontSize: 13 }}>
                            {selected ? `${selected.requisition_id} — ${selected.job_title}` : selectedId}
                        </span>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className="flex flex-col" style={{ maxWidth: 480 }}>
            <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold leading-tight">
                    Open Requisitions
                </CardTitle>
                <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                    Select a requisition to create a job description
                </div>
            </CardHeader>
            <CardContent className="space-y-2">
                {requisitions.map((req) => (
                    <SingleRequisition
                        key={req.requisition_id}
                        req={req}
                        isSelected={selectedId === req.requisition_id}
                        onSelect={handleSelect}
                    />
                ))}
            </CardContent>
        </Card>
    )
}
