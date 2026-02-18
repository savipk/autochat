import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, AlertCircle } from "lucide-react"

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
                <Progress value={completionScore} className="h-2 mt-2" />
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
                                    <AlertCircle className="h-3.5 w-3.5 text-destructive" />
                                ) : (
                                    <CheckCircle className="h-3.5 w-3.5 text-primary" />
                                )}
                                <span>{label}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-muted-foreground text-xs">
                                    {score}/{max}
                                </span>
                                {isMissing && (
                                    <Badge variant="outline" className="text-xs text-destructive">
                                        Missing
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
