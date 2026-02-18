import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Briefcase, MapPin, Building2, Calendar, User, ThumbsUp } from "lucide-react"

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

export default function JobCard() {
    const title = props.title || "Unknown Position"
    const corporateTitle = props.corporateTitle || ""
    const corporateTitleCode = props.corporateTitleCode || ""
    const hiringManager = props.hiringManager || ""
    const orgLine = props.orgLine || ""
    const country = props.country || ""
    const isNew = props.isNew || false
    const daysAgo = props.daysAgo
    const matchReason = props.matchReason || ""
    const matchingSkills = props.matchingSkills || []
    const jobId = props.id || ""

    const corporateDisplay = corporateTitleCode
        ? `${corporateTitle} (${corporateTitleCode})`
        : corporateTitle
    const initials = getInitials(hiringManager)
    const postedText = formatDaysAgo(daysAgo)

    return (
        <Card className="w-full max-w-sm relative">
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
            <CardContent className="space-y-3">
                <div className="space-y-1 text-sm text-muted-foreground">
                    {corporateDisplay && (
                        <div className="flex items-center gap-2">
                            <Briefcase className="h-3.5 w-3.5" />
                            <span>{corporateDisplay}</span>
                        </div>
                    )}
                    {orgLine && (
                        <div className="flex items-center gap-2">
                            <Building2 className="h-3.5 w-3.5" />
                            <span>{orgLine}</span>
                        </div>
                    )}
                    {country && (
                        <div className="flex items-center gap-2">
                            <MapPin className="h-3.5 w-3.5" />
                            <span>{country}</span>
                        </div>
                    )}
                    {postedText && (
                        <div className="flex items-center gap-2">
                            <Calendar className="h-3.5 w-3.5" />
                            <span>{postedText}</span>
                        </div>
                    )}
                </div>

                {hiringManager && (
                    <div className="flex items-center gap-2 pt-2 border-t">
                        <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-xs font-semibold flex-shrink-0">
                            {initials}
                        </div>
                        <div className="flex flex-col min-w-0">
                            <span className="text-xs text-muted-foreground">Hiring manager</span>
                            <span className="text-sm font-medium truncate">{hiringManager}</span>
                        </div>
                    </div>
                )}

                {matchReason && (
                    <div className="bg-muted rounded-md p-2 text-xs leading-relaxed">
                        {matchReason.length > 100 ? matchReason.slice(0, 100) + "..." : matchReason}
                    </div>
                )}

                {matchingSkills.length > 0 && (
                    <div>
                        <div className="text-xs text-muted-foreground mb-1">Matching skills</div>
                        <div className="flex flex-wrap gap-1">
                            {matchingSkills.slice(0, 3).map((skill, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                    {skill}
                                </Badge>
                            ))}
                        </div>
                    </div>
                )}

                <div className="flex gap-2 pt-2 border-t">
                    <Button
                        size="sm"
                        className="text-xs"
                        onClick={() => sendUserMessage(`Tell me more about the ${title} role (${jobId})`)}
                    >
                        Ask about role
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        className="text-xs"
                        onClick={() => sendUserMessage(`Draft a message to ${hiringManager} about the ${title} role`)}
                    >
                        Draft message
                    </Button>
                    <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs px-2"
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
