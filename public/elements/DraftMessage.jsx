import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Send, Edit, User } from "lucide-react"

export default function DraftMessage() {
    const recipientName = props.recipient_name || "Recipient"
    const senderName = props.sender_name || "You"
    const messageBody = props.message_body || ""
    const jobTitle = props.job_title || ""
    const messageType = props.message_type || "teams"

    return (
        <Card className="w-full max-w-lg">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Send className="h-4 w-4" />
                        {messageType === "teams" ? "Teams Message" : "Email"} Draft
                    </CardTitle>
                    {jobTitle && (
                        <span className="text-xs text-muted-foreground">
                            Re: {jobTitle}
                        </span>
                    )}
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1.5">
                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground">From:</span>
                        <span className="font-medium">{senderName}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground">To:</span>
                        <span className="font-medium">{recipientName}</span>
                    </div>
                </div>

                <div className="bg-muted rounded-md p-3 text-sm leading-relaxed whitespace-pre-wrap">
                    {messageBody}
                </div>

                <div className="flex gap-2">
                    <Button
                        size="sm"
                        className="text-xs"
                        onClick={() => sendUserMessage("Send the message")}
                    >
                        <Send className="h-3.5 w-3.5 mr-1" />
                        Send
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        className="text-xs"
                        onClick={() => sendUserMessage("Edit the message")}
                    >
                        <Edit className="h-3.5 w-3.5 mr-1" />
                        Edit
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
