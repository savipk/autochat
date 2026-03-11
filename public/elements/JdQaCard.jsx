import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function JdQaCard() {
    const jobId = props.jobId || ""
    const jobTitle = props.jobTitle || ""
    const hiringManager = props.hiringManager || ""
    const orgLine = props.orgLine || ""
    const citations = props.citations || []
    const suggestContactHiringManager = props.suggestContactHiringManager || false

    return (
        <Card className="w-full" style={{ borderLeft: "3px solid #6264A7" }}>
            <CardContent className="space-y-2 pt-4">
                {jobId && (
                    <div className="text-sm text-muted-foreground">
                        <span className="font-medium" style={{ color: "#6264A7" }}>Job ID:</span> {jobId}
                    </div>
                )}
                {jobTitle && (
                    <div className="text-sm">
                        <span className="font-medium">Role:</span> {jobTitle}
                    </div>
                )}
                {hiringManager && (
                    <div className="text-sm">
                        <span className="font-medium">Hiring Manager:</span> {hiringManager}
                    </div>
                )}
                {orgLine && (
                    <div className="text-sm">
                        <span className="font-medium">Org:</span> {orgLine}
                    </div>
                )}
                {citations.length > 0 && (
                    <div className="text-sm text-muted-foreground">
                        <span className="font-medium">Sources:</span> {citations.join(", ")}
                    </div>
                )}
                {suggestContactHiringManager && hiringManager && (
                    <div className="pt-2 border-t">
                        <Button
                            size="sm"
                            className="text-xs font-medium rounded"
                            style={{ backgroundColor: "#6264A7", color: "#fff" }}
                            onClick={() => window.populateChatInput(`Draft a message to ${hiringManager} about the ${jobTitle} role`)}
                        >
                            Message Hiring Manager
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
