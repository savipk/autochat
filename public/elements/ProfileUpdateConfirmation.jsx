import { useState } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { UserPen, Check, X, ArrowRight } from "lucide-react"

function SkillBadges({ skills, variant = "default" }) {
    if (!skills || skills.length === 0) return <span className="text-xs text-muted-foreground">None</span>
    return (
        <div className="flex flex-wrap gap-1">
            {skills.map((skill, i) => {
                const name = typeof skill === "object" ? skill.name || JSON.stringify(skill) : String(skill)
                return (
                    <Badge key={i} variant={variant} className="text-xs">
                        {name}
                    </Badge>
                )
            })}
        </div>
    )
}

function ExperienceEntry({ entry }) {
    return (
        <div className="text-sm border-l-2 pl-2 py-0.5" style={{ borderColor: "#6264A7" }}>
            <div className="font-medium">{entry.jobTitle || "Untitled Role"}</div>
            {entry.company && <div className="text-xs text-muted-foreground">{entry.company}</div>}
            {(entry.startDate || entry.endDate) && (
                <div className="text-xs text-muted-foreground">
                    {entry.startDate || "?"} &mdash; {entry.endDate || "Present"}
                </div>
            )}
        </div>
    )
}

function EducationEntry({ entry }) {
    return (
        <div className="text-sm border-l-2 pl-2 py-0.5" style={{ borderColor: "#6264A7" }}>
            <div className="font-medium">{entry.institutionName || "Unknown Institution"}</div>
            {entry.degree && <div className="text-xs text-muted-foreground">{entry.degree}</div>}
            {entry.areaOfStudy && <div className="text-xs text-muted-foreground">{entry.areaOfStudy}</div>}
        </div>
    )
}

function renderSectionData(section, data) {
    if (!data || (typeof data === "object" && Object.keys(data).length === 0)) {
        return <span className="text-xs text-muted-foreground">Empty</span>
    }

    if (section === "skills") {
        const top = data.topSkills || data.top || []
        const additional = data.additionalSkills || data.additional || []
        return (
            <div className="space-y-1">
                {top.length > 0 && (
                    <div>
                        <span className="text-xs text-muted-foreground">Top: </span>
                        <SkillBadges skills={top} />
                    </div>
                )}
                {additional.length > 0 && (
                    <div>
                        <span className="text-xs text-muted-foreground">Additional: </span>
                        <SkillBadges skills={additional} />
                    </div>
                )}
            </div>
        )
    }

    if (section === "experience") {
        const experiences = data.experiences || (Array.isArray(data) ? data : [])
        if (experiences.length > 0) {
            return (
                <div className="space-y-1">
                    {experiences.map((exp, i) => <ExperienceEntry key={i} entry={exp} />)}
                </div>
            )
        }
    }

    if (section === "education" || section === "qualification") {
        const educations = data.educations || (Array.isArray(data) ? data : [])
        if (educations.length > 0) {
            return (
                <div className="space-y-1">
                    {educations.map((edu, i) => <EducationEntry key={i} entry={edu} />)}
                </div>
            )
        }
    }

    // Generic fallback
    return (
        <div className="space-y-1">
            {Object.entries(data).map(([field, value]) => (
                <div key={field} className="text-sm">
                    <span className="font-medium">{field}:</span>{" "}
                    <span className="text-muted-foreground">
                        {Array.isArray(value) ? value.map(v => typeof v === "object" ? (v.name || v.description || JSON.stringify(v)) : String(v)).join(", ") : String(value)}
                    </span>
                </div>
            ))}
        </div>
    )
}

export default function ProfileUpdateConfirmation() {
    const section = props.section || "profile"
    const updatedFields = props.updated_fields || {}
    const currentValues = props.current_values || null
    const previousScore = props.previous_completion_score || 0
    const estimatedScore = props.estimated_new_score || 0
    const payload = props.payload || "{}"

    const [status, setStatus] = useState("pending") // pending | accepted | declined

    function handleAccept() {
        callAction({ name: "approve_profile_update", payload: JSON.parse(payload) })
        setStatus("accepted")
    }

    function handleDecline() {
        callAction({ name: "reject_profile_update", payload: JSON.parse(payload) })
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

    const isRollback = section === "rollback"
    const headerText = isRollback ? "Profile Rollback Request" : "Profile Update Request"
    const subText = isRollback
        ? "The assistant wants to restore your profile from backup"
        : <>The assistant wants to update your <strong>{section}</strong> section</>
    const hasCurrentData = currentValues && Object.keys(currentValues).length > 0

    return (
        <Card className="w-full max-w-lg">
            <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <UserPen className="h-4 w-4" />
                    {headerText}
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1">
                    {subText}
                </p>
            </CardHeader>
            <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <div className="text-xs font-medium text-muted-foreground mb-1">Current</div>
                        <div className="bg-muted/50 rounded p-2">
                            {hasCurrentData
                                ? renderSectionData(section, currentValues)
                                : <span className="text-xs text-muted-foreground italic">No current data</span>
                            }
                        </div>
                    </div>
                    <div>
                        <div className="text-xs font-medium mb-1" style={{ color: "#6264A7" }}>
                            {isRollback ? "Backup (Restore To)" : "Proposed"}
                        </div>
                        <div className="rounded p-2 border" style={{ borderColor: "#6264A7" }}>
                            {renderSectionData(section, updatedFields)}
                        </div>
                    </div>
                </div>

                {(previousScore > 0 || estimatedScore > 0) && (
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                        Completion score: {previousScore}%
                        <ArrowRight className="h-3 w-3" />
                        {estimatedScore}%
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
