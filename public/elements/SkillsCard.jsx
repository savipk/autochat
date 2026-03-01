import { useState } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Sparkles, Save, Check } from "lucide-react"

export default function SkillsCard() {
    const topSkills = props.topSkills || []
    const additionalSkills = props.additionalSkills || []
    const confidence = props.confidence || 0

    const [selectedTop, setSelectedTop] = useState(() => new Set(topSkills))
    const [selectedAdditional, setSelectedAdditional] = useState(() => new Set(additionalSkills))
    const [customInput, setCustomInput] = useState("")
    const [isSaved, setIsSaved] = useState(false)

    function toggleSkill(skill, selected, setSelected) {
        const next = new Set(selected)
        if (next.has(skill)) {
            next.delete(skill)
        } else {
            next.add(skill)
        }
        setSelected(next)
    }

    function handleSave() {
        const all = []
        topSkills.forEach(s => { if (selectedTop.has(s)) all.push(s) })
        additionalSkills.forEach(s => { if (selectedAdditional.has(s)) all.push(s) })

        if (customInput.trim()) {
            customInput.split(",").forEach(s => {
                const trimmed = s.trim()
                if (trimmed && !all.includes(trimmed)) {
                    all.push(trimmed)
                }
            })
        }

        if (all.length > 0) {
            sendUserMessage(`Save these skills to my profile: ${all.join(", ")}`)
        }
        setIsSaved(true)
    }

    const confidencePercent = Math.round(confidence * 100)

    return (
        <Card className="w-full max-w-md">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                        <Sparkles className="h-4 w-4" />
                        Suggested Skills
                    </CardTitle>
                    {confidence > 0 && (
                        <span className="text-xs text-muted-foreground">
                            {confidencePercent}% confidence
                        </span>
                    )}
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {topSkills.length > 0 && (
                    <div>
                        <div className="text-xs text-muted-foreground mb-2">Top Skills</div>
                        <div className="flex flex-wrap gap-1.5">
                            {topSkills.map((skill) => (
                                <Button
                                    key={skill}
                                    size="sm"
                                    variant={selectedTop.has(skill) ? "default" : "outline"}
                                    className="text-xs h-7"
                                    disabled={isSaved}
                                    onClick={() => toggleSkill(skill, selectedTop, setSelectedTop)}
                                >
                                    {skill}
                                </Button>
                            ))}
                        </div>
                    </div>
                )}

                {additionalSkills.length > 0 && (
                    <div>
                        <div className="text-xs text-muted-foreground mb-2">Additional Skills</div>
                        <div className="flex flex-wrap gap-1.5">
                            {additionalSkills.map((skill) => (
                                <Button
                                    key={skill}
                                    size="sm"
                                    variant={selectedAdditional.has(skill) ? "default" : "outline"}
                                    className="text-xs h-7"
                                    disabled={isSaved}
                                    onClick={() => toggleSkill(skill, selectedAdditional, setSelectedAdditional)}
                                >
                                    {skill}
                                </Button>
                            ))}
                        </div>
                    </div>
                )}

                <div>
                    <Input
                        placeholder="e.g. Python, Leadership, Agile"
                        value={customInput}
                        onChange={(e) => setCustomInput(e.target.value)}
                        disabled={isSaved}
                        className="text-sm"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Separate with commas</p>
                </div>

                <Button
                    className="w-full"
                    disabled={isSaved}
                    onClick={handleSave}
                >
                    {isSaved ? (
                        <>
                            <Check className="h-4 w-4 mr-2" />
                            Saved!
                        </>
                    ) : (
                        <>
                            <Save className="h-4 w-4 mr-2" />
                            Save to Profile
                        </>
                    )}
                </Button>
            </CardContent>
        </Card>
    )
}
