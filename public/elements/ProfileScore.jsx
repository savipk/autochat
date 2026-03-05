import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle, AlertCircle, Plus } from "lucide-react"

const SECTION_ACTIONS = {
    experience: "Add an experience to my profile",
    qualification: "Add education to my profile",
    skills: "Analyze my skills",
    careerAspirationPreference: "Update my career aspirations",
    careerLocationPreference: "Update my location preferences",
    careerRolePreference: "Update my role preferences",
    language: "Add a language to my profile",
}

export default function ProfileScore() {
    const completionScore = props.completionScore || 0
    const sectionScores = props.sectionScores || {}
    const missingSections = props.missingSections || []

    const sections = [
        { key: "experience", label: "Experience", max: 25 },
        { key: "qualification", label: "Qualification", max: 15 },
        { key: "skills", label: "Skills", max: 20 },
        { key: "careerAspirationPreference", label: "Career Aspirations", max: 10 },
        { key: "careerLocationPreference", label: "Location Preference", max: 10 },
        { key: "careerRolePreference", label: "Role Preference", max: 10 },
        { key: "language", label: "Languages", max: 10 },
    ]

    function handleAddSection(key) {
        const message = SECTION_ACTIONS[key]
        if (message) {
            window.populateChatInput(message)
        }
    }

    return (
        <Card className="w-full max-w-md">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold">
                        Profile Score
                    </CardTitle>
                    <span className="text-2xl font-bold">
                        {completionScore}%
                    </span>
                </div>
                <div className="h-2 mt-2 w-full rounded-full bg-muted overflow-hidden">
                    <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${completionScore}%`, backgroundColor: "#6264A7" }}
                    />
                </div>
            </CardHeader>
            <CardContent className="space-y-2">
                {sections.map(({ key, label, max }) => {
                    const score = sectionScores[key] || 0
                    const isMissing = missingSections.includes(key) || missingSections.includes(label.toLowerCase())
                    const pct = max > 0 ? Math.round((score / max) * 100) : 0

                    return (
                        <div key={key} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                                {isMissing ? (
                                    <AlertCircle className="h-3.5 w-3.5" style={{ color: "#6264A7" }} />
                                ) : (
                                    <CheckCircle className="h-3.5 w-3.5" style={{ color: "#6264A7" }} />
                                )}
                                <span>{label}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-muted-foreground text-xs">
                                    {score}/{max}
                                </span>
                                {isMissing ? (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-6 px-2 text-xs rounded"
                                        style={{ color: "#6264A7" }}
                                        onClick={() => handleAddSection(key)}
                                    >
                                        <Plus className="h-3 w-3 mr-1" />
                                        Add
                                    </Button>
                                ) : (
                                    <Badge variant="outline" className="text-xs" style={{ borderColor: "#6264A7", color: "#6264A7" }}>
                                        Done
                                    </Badge>
                                )}
                            </div>
                        </div>
                    )
                })}
            </CardContent>
        </Card>
    )
}
