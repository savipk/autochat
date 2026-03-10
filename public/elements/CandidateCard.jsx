import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

function getInitials(name) {
    if (!name) return "??"
    return name.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase()
}

function SingleCandidateCard({ candidate }) {
    const name = candidate.name || "Unknown"
    const title = candidate.businessTitle || ""
    const rank = candidate.rank || {}
    const rankCode = typeof rank === "object" ? rank.code : rank
    const location = candidate.location || ""
    const department = candidate.department || ""
    const yearsAtCompany = candidate.yearsAtCompany
    const skills = candidate.skills || []
    const matchScore = candidate.matchScore
    const employeeId = candidate.employeeId || ""
    const initials = getInitials(name)

    const maxSkills = 5
    const visibleSkills = skills.slice(0, maxSkills)
    const overflowCount = skills.length - maxSkills

    return (
        <Card className="relative flex flex-col" style={{ minWidth: 0, flex: "1 1 0" }}>
            {matchScore !== undefined && matchScore !== null && matchScore > 0 && (
                <div className="absolute top-3 right-3">
                    <Badge
                        className="text-xs"
                        style={{ backgroundColor: "#6264A7", color: "#fff" }}
                    >
                        Score: {matchScore}
                    </Badge>
                </div>
            )}

            <CardHeader className="pb-2">
                <div className="flex items-center gap-3">
                    <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0"
                        style={{ backgroundColor: "#6264A7", color: "#fff" }}
                    >
                        {initials}
                    </div>
                    <div className="min-w-0">
                        <CardTitle className="text-base font-semibold leading-tight pr-16">
                            {name}
                        </CardTitle>
                        <div className="text-sm text-muted-foreground truncate">{title}</div>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="space-y-3 flex-1 flex flex-col">
                <div className="flex items-center gap-2 flex-wrap">
                    {rankCode && (
                        <Badge variant="outline" className="text-xs"
                            style={{ borderColor: "#6264A7", color: "#6264A7" }}>
                            {rankCode}
                        </Badge>
                    )}
                </div>

                <div className="space-y-1 text-sm text-muted-foreground">
                    {location && (
                        <div className="flex items-center gap-2">
                            <span className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0"
                                style={{ backgroundColor: "#C4314B" }} />
                            <span>{location}</span>
                        </div>
                    )}
                    {department && (
                        <div className="flex items-center gap-2">
                            <span className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0"
                                style={{ backgroundColor: "#4A4A4A" }} />
                            <span>{department}</span>
                        </div>
                    )}
                    {yearsAtCompany !== undefined && yearsAtCompany !== null && (
                        <div className="flex items-center gap-2">
                            <span className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0"
                                style={{ backgroundColor: "#8B5CF6" }} />
                            <span>{yearsAtCompany} years at company</span>
                        </div>
                    )}
                </div>

                {visibleSkills.length > 0 && (
                    <div>
                        <div className="text-xs text-muted-foreground mb-1">Skills</div>
                        <div className="flex flex-wrap gap-1">
                            {visibleSkills.map((skill, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                    {skill}
                                </Badge>
                            ))}
                            {overflowCount > 0 && (
                                <Badge variant="secondary" className="text-xs"
                                    style={{ opacity: 0.7 }}>
                                    +{overflowCount} more
                                </Badge>
                            )}
                        </div>
                    </div>
                )}

                <div className="flex gap-2 pt-2 border-t mt-auto">
                    <Button
                        size="sm"
                        variant="outline"
                        className="text-xs font-medium rounded"
                        style={{ borderColor: "#6264A7", color: "#6264A7" }}
                        onClick={() => window.populateChatInput(`View profile for ${employeeId}`)}
                    >
                        View Profile
                    </Button>
                    <Button
                        size="sm"
                        className="text-xs font-medium rounded"
                        style={{ backgroundColor: "#6264A7", color: "#fff" }}
                        onClick={() => window.populateChatInput(`Draft a message to ${name}`)}
                    >
                        Message
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

export default function CandidateCard() {
    const candidates = props.candidates || []
    const totalAvailable = props.totalAvailable
    const hasMore = props.hasMore

    if (candidates.length === 0) {
        return null
    }

    return (
        <div className="space-y-3 w-full" style={{ maxWidth: "100%" }}>
            {totalAvailable !== undefined && totalAvailable !== null && (
                <div className="text-sm text-muted-foreground font-medium">
                    Showing {candidates.length} of {totalAvailable} candidates
                </div>
            )}
            <div className="flex gap-4 w-full">
                {candidates.map((candidate, i) => (
                    <SingleCandidateCard key={candidate.employeeId || i} candidate={candidate} />
                ))}
            </div>
            {hasMore && (
                <div className="flex justify-center pt-2">
                    <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs font-medium rounded"
                        style={{ color: "#6264A7" }}
                        onClick={() => window.populateChatInput("Show more candidates")}
                    >
                        Show more candidates
                    </Button>
                </div>
            )}
        </div>
    )
}
