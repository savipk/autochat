import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function SendConfirmation() {
    const recipientName = props.recipientName || ""
    const messageType = props.messageType || "teams"
    const sentAt = props.sentAt || ""
    const jobContext = props.jobContext || null
    const suggestApply = props.suggestApply || false

    const channelLabel = messageType === "email" ? "Email" : "Teams"

    return (
        <Card className="w-full" style={{ borderLeft: "3px solid #13A10E" }}>
            <CardContent className="space-y-2 pt-4">
                <div className="flex items-center gap-2">
                    <span className="text-base font-semibold" style={{ color: "#13A10E" }}>
                        &#10003; Message Sent
                    </span>
                </div>
                {recipientName && (
                    <div className="text-sm">
                        <span className="font-medium">To:</span> {recipientName}
                        <span className="text-muted-foreground ml-3">Via: {channelLabel}</span>
                    </div>
                )}
                {sentAt && (
                    <div className="text-sm text-muted-foreground">
                        <span className="font-medium">Sent:</span> {sentAt}
                    </div>
                )}
                {jobContext && jobContext.job_title && (
                    <div className="text-sm">
                        <span className="font-medium">Role:</span> {jobContext.job_title}
                    </div>
                )}
                {suggestApply && jobContext && jobContext.job_title && (
                    <div className="pt-2 border-t">
                        <Button
                            size="sm"
                            className="text-xs font-medium rounded"
                            style={{ backgroundColor: "#6264A7", color: "#fff" }}
                            onClick={() => window.populateChatInput(`Apply for the ${jobContext.job_title} role`)}
                        >
                            Apply for Role
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
