import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ThumbsUp } from "lucide-react"

function getInitials(name) {
    if (!name) return "HM"
    return name.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase()
}

function formatDaysAgo(days) {
    if (days === null || days === undefined) return ""
    if (days === 0) return "Posted today"
    if (days === 1) return "Posted 1 day ago"
    return `Posted ${days} days ago`
}

function DetailRow({ color, children }) {
    return (
        <div className="flex items-center gap-2">
            <span
                className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0"
                style={{ backgroundColor: color }}
            />
            <span>{children}</span>
        </div>
    )
}

function SingleJobCard({ job }) {
    const title = job.title || "Unknown Position"
    const corporateTitle = job.corporateTitle || ""
    const corporateTitleCode = job.corporateTitleCode || ""
    const hiringManager = job.hiringManager || ""
    const orgLine = job.orgLine || ""
    const country = job.country || ""
    const isNew = job.isNew || false
    const daysAgo = job.daysAgo
    const matchReason = job.matchReason || ""
    const matchingSkills = job.matchingSkills || []
    const jobId = job.id || ""

    const corporateDisplay = corporateTitleCode
        ? `${corporateTitle} (${corporateTitleCode})`
        : corporateTitle
    const initials = getInitials(hiringManager)
    const postedText = formatDaysAgo(daysAgo)

    return (
        <Card className="relative flex flex-col" style={{ minWidth: 0, flex: "1 1 0" }}>
            {isNew && (
                <Badge variant="destructive" className="absolute top-3 right-3 text-xs">
                    New
                </Badge>
            )}
            <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold pr-12 leading-tight">
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 flex-1 flex flex-col">
                <div className="space-y-1 text-sm text-muted-foreground">
                    {corporateDisplay && (
                        <DetailRow color="#6264A7">{corporateDisplay}</DetailRow>
                    )}
                    {orgLine && (
                        <DetailRow color="#4A4A4A">{orgLine}</DetailRow>
                    )}
                    {country && (
                        <DetailRow color="#C4314B">{country}</DetailRow>
                    )}
                    {postedText && (
                        <DetailRow color="#8B5CF6">{postedText}</DetailRow>
                    )}
                </div>

                {hiringManager && (
                    <div className="flex items-center gap-2 pt-2 border-t">
                        <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-xs font-semibold flex-shrink-0"
                            style={{ backgroundColor: "#6264A7" }}>
                            {initials}
                        </div>
                        <div className="flex flex-col min-w-0">
                            <span className="text-xs text-muted-foreground">Hiring manager</span>
                            <span className="text-sm font-medium truncate">{hiringManager}</span>
                        </div>
                    </div>
                )}

                {matchReason && (
                    <div className="text-xs text-muted-foreground leading-relaxed">
                        {matchReason.length > 120 ? matchReason.slice(0, 120) + "..." : matchReason}
                    </div>
                )}

                {matchingSkills.length > 0 && (
                    <div>
                        <div className="text-xs text-muted-foreground mb-1">Matching skills</div>
                        <div className="flex flex-wrap gap-1">
                            {matchingSkills.slice(0, 3).map((skill, i) => (
                                <Badge key={i} variant="secondary" className="text-xs"
                                    style={{ textDecoration: "underline", textUnderlineOffset: "2px" }}>
                                    {skill}
                                </Badge>
                            ))}
                        </div>
                    </div>
                )}

                <div className="flex gap-2 pt-2 border-t mt-auto">
                    <Button
                        size="sm"
                        className="text-xs font-medium rounded"
                        style={{ backgroundColor: "#6264A7", color: "#fff" }}
                        onClick={() => sendUserMessage(`Tell me more about the ${title} role (${jobId})`)}
                    >
                        View
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        className="text-xs font-medium rounded"
                        style={{ borderColor: "#6264A7", color: "#6264A7" }}
                        onClick={() => sendUserMessage(`Save the ${title} role (${jobId}) to my favorites`)}
                    >
                        Save
                    </Button>
                    <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs px-2 rounded"
                        style={{ color: "#C4314B" }}
                    >
                        <ThumbsUp className="h-3.5 w-3.5" />
                    </Button>
                </div>

                <div className="text-xs text-muted-foreground">
                    ID: {jobId}
                </div>
            </CardContent>
        </Card>
    )
}

export default function JobCard() {
    const jobs = props.jobs || []

    if (jobs.length === 0) {
        return null
    }

    return (
        <div className="flex gap-4 w-full" style={{ maxWidth: "100%" }}>
            {jobs.map((job, i) => (
                <SingleJobCard key={job.id || i} job={job} />
            ))}
        </div>
    )
}
