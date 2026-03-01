import { useState } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { UserPen, Check, X } from "lucide-react"

export default function ProfileUpdateConfirmation() {
    const section = props.section || "profile"
    const updatedFields = props.updated_fields || {}
    const previousScore = props.previous_completion_score || 0
    const estimatedScore = props.estimated_new_score || 0
    const payload = props.payload || "{}"

    const [status, setStatus] = useState("pending") // pending | accepted | declined

    function handleAccept() {
        callAction("approve_profile_update", payload)
        setStatus("accepted")
    }

    function handleDecline() {
        callAction("reject_profile_update", payload)
        setStatus("declined")
    }

    if (status === "accepted") {
        return (
            <Card className="w-full max-w-md">
                <CardContent className="py-3 flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4" style={{ color: "#10b981" }} />
                    <span>Profile updated: <strong>{section}</strong> section saved.</span>
                </CardContent>
            </Card>
        )
    }

    if (status === "declined") {
        return (
            <Card className="w-full max-w-md">
                <CardContent className="py-3 flex items-center gap-2 text-sm text-muted-foreground">
                    <X className="h-4 w-4" />
                    <span>Update declined. No changes were made.</span>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className="w-full max-w-md">
            <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <UserPen className="h-4 w-4" />
                    Profile Update Request
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1">
                    The assistant wants to update your <strong>{section}</strong> section
                </p>
            </CardHeader>
            <CardContent className="space-y-3">
                <div className="space-y-1">
                    {Object.entries(updatedFields).map(([field, value]) => (
                        <div key={field} className="text-sm">
                            <span className="font-medium">{field}:</span>{" "}
                            <span className="text-muted-foreground">
                                {Array.isArray(value) ? value.join(", ") : String(value)}
                            </span>
                        </div>
                    ))}
                </div>

                {(previousScore > 0 || estimatedScore > 0) && (
                    <div className="text-xs text-muted-foreground">
                        Completion score: {previousScore}% &rarr; {estimatedScore}%
                    </div>
                )}

                <div className="flex gap-2 pt-1">
                    <Button
                        className="flex-1 font-medium rounded"
                        style={{ backgroundColor: "#6264A7", color: "#fff" }}
                        onClick={handleAccept}
                    >
                        <Check className="h-4 w-4 mr-2" />
                        Accept
                    </Button>
                    <Button
                        variant="outline"
                        className="flex-1 font-medium rounded"
                        style={{ borderColor: "#6264A7", color: "#6264A7" }}
                        onClick={handleDecline}
                    >
                        <X className="h-4 w-4 mr-2" />
                        Decline
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
