import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function JdFinalizedCard() {
    const finalizedAt = props.finalizedAt || ""
    const nextSteps = props.nextSteps || []

    return (
        <Card className="w-full" style={{ borderLeft: "3px solid #13A10E" }}>
            <CardContent className="space-y-2 pt-4">
                <div className="flex items-center gap-2">
                    <span className="text-base font-semibold" style={{ color: "#13A10E" }}>
                        &#10003; Job Description Finalized
                    </span>
                </div>
                {finalizedAt && (
                    <div className="text-sm text-muted-foreground">
                        <span className="font-medium">Finalized at:</span> {finalizedAt}
                    </div>
                )}
                {nextSteps.length > 0 && (
                    <div className="text-sm">
                        <div className="font-medium mb-1">Next Steps:</div>
                        <ul className="list-disc list-inside space-y-0.5 text-muted-foreground">
                            {nextSteps.map((step, i) => (
                                <li key={i}>{step}</li>
                            ))}
                        </ul>
                    </div>
                )}
                <div className="pt-2 border-t">
                    <Button
                        size="sm"
                        className="text-xs font-medium rounded"
                        style={{ backgroundColor: "#6264A7", color: "#fff" }}
                        onClick={() => window.populateChatInput("Search for candidates for this role")}
                    >
                        Search for Candidates
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
