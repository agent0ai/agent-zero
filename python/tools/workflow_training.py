"""
Workflow Training Tool - Skill development and learning progression management
Manages training modules, assessments, and agent proficiency tracking
"""

from python.helpers.tool import Tool, Response
from python.helpers import files


class WorkflowTraining(Tool):
    """
    Tool for managing training programs, lessons, and skill assessments.

    Provides structured learning paths with:
    - Training modules with lessons
    - Practice tasks and assessments
    - Proficiency tracking and certification
    - Skill prerequisites and progressions
    """

    def __init__(self, agent, name: str, args: dict, message: str, **kwargs):
        super().__init__(agent, name, args, message, **kwargs)

        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager

        db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflows.db")
        self.manager = WorkflowEngineManager(db_path)
        self.agent_id = str(agent.number) if hasattr(agent, 'number') else "agent_0"

    async def execute(self, **kwargs):
        action = self.args.get("action", "").lower()

        action_map = {
            # Skill Management
            "define_skill": self._define_skill,
            "get_skill": self._get_skill,
            "list_skills": self._list_skills,
            "assess_skill": self._assess_skill,
            "get_proficiency": self._get_proficiency,

            # Training Modules
            "create_module": self._create_module,
            "get_module": self._get_module,
            "start_lesson": self._start_lesson,
            "complete_lesson": self._complete_lesson,

            # Learning Paths
            "create_path": self._create_path,
            "list_paths": self._list_paths,
            "get_path": self._get_path,
            "enroll_path": self._enroll_path,
            "get_progress": self._get_progress,

            # Practice & Assessment
            "practice_task": self._practice_task,
            "take_assessment": self._take_assessment,
            "get_recommendations": self._get_recommendations,

            # Reporting
            "skill_report": self._skill_report,
            "training_dashboard": self._training_dashboard,
        }

        handler = action_map.get(action)
        if handler:
            return await handler()

        return Response(
            message=self._format_help(),
            break_loop=False
        )

    # ========== Skill Management ==========

    async def _define_skill(self):
        """Define a new skill with proficiency levels"""
        # Build proficiency levels from input or use defaults
        levels = self.args.get("proficiency_levels")
        if not levels:
            levels = [
                {"level": 1, "name": "novice", "criteria": ["Basic understanding"], "min_completions": 0},
                {"level": 2, "name": "beginner", "criteria": ["Can perform with guidance"], "min_completions": 5},
                {"level": 3, "name": "intermediate", "criteria": ["Can perform independently"], "min_completions": 15},
                {"level": 4, "name": "advanced", "criteria": ["Can optimize and improve"], "min_completions": 30},
                {"level": 5, "name": "expert", "criteria": ["Can teach and innovate"], "min_completions": 50}
            ]

        result = self.manager.register_skill(
            skill_id=self.args.get("skill_id"),
            name=self.args.get("name"),
            category=self.args.get("category", "technical"),
            description=self.args.get("description"),
            proficiency_levels=levels,
            prerequisites=self.args.get("prerequisites", []),
            related_tools=self.args.get("related_tools", [])
        )
        return Response(
            message=self._format_skill_result(result),
            break_loop=False
        )

    async def _get_skill(self):
        """Get skill details"""
        result = self.manager.get_skill(
            skill_id=self.args.get("skill_id")
        )
        return Response(
            message=self._format_skill_details(result),
            break_loop=False
        )

    async def _list_skills(self):
        """List all available skills"""
        result = self.manager.list_skills(
            category=self.args.get("category")
        )
        return Response(
            message=self._format_skills_list(result),
            break_loop=False
        )

    async def _assess_skill(self):
        """Record a skill assessment or practice"""
        result = self.manager.track_skill_usage(
            agent_id=self.args.get("agent_id", self.agent_id),
            skill_id=self.args.get("skill_id"),
            success=self.args.get("success", True),
            assessment_score=self.args.get("score")
        )
        return Response(
            message=self._format_assessment_result(result),
            break_loop=False
        )

    async def _get_proficiency(self):
        """Get agent's skill proficiency"""
        result = self.manager.get_agent_skills(
            agent_id=self.args.get("agent_id", self.agent_id)
        )
        return Response(
            message=self._format_proficiency(result),
            break_loop=False
        )

    # ========== Training Modules ==========

    async def _create_module(self):
        """Create a training module with lessons"""
        module_id = self.args.get("module_id")
        name = self.args.get("name")
        lessons = self.args.get("lessons", [])
        skills_taught = self.args.get("skills_taught", [])

        # Store module via DB (use the same workflow database)
        self.manager.db.conn = self.manager.db._get_conn()
        cursor = self.manager.db.conn.cursor()

        import json
        cursor.execute("""
            INSERT INTO training_modules (module_id, name, description, skills_taught,
                                         skill_level_target, lessons, module_assessment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(module_id) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                skills_taught = excluded.skills_taught,
                lessons = excluded.lessons
        """, (
            module_id, name,
            self.args.get("description"),
            json.dumps(skills_taught),
            self.args.get("skill_level_target", 2),
            json.dumps(lessons),
            json.dumps(self.args.get("assessment"))
        ))

        self.manager.db.conn.commit()
        self.manager.db.conn.close()

        return Response(
            message=f"## Training Module Created\n\n**Module:** {name}\n**ID:** {module_id}\n**Lessons:** {len(lessons)}\n**Skills:** {', '.join(skills_taught)}",
            break_loop=False
        )

    async def _get_module(self):
        """Get module details"""
        module_id = self.args.get("module_id")

        conn = self.manager.db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM training_modules WHERE module_id = ?", (module_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return Response(message=f"Module not found: {module_id}", break_loop=False)

        import json
        module = dict(row)
        module['skills_taught'] = json.loads(module['skills_taught'])
        module['lessons'] = json.loads(module['lessons'])

        return Response(
            message=self._format_module(module),
            break_loop=False
        )

    async def _start_lesson(self):
        """Start a lesson from a module"""
        module_id = self.args.get("module_id")
        lesson_id = self.args.get("lesson_id")

        # Get lesson content
        conn = self.manager.db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT lessons FROM training_modules WHERE module_id = ?", (module_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return Response(message=f"Module not found: {module_id}", break_loop=False)

        import json
        lessons = json.loads(row['lessons'])
        lesson = next((l for l in lessons if l.get('id') == lesson_id), None)

        if not lesson:
            return Response(message=f"Lesson not found: {lesson_id}", break_loop=False)

        return Response(
            message=self._format_lesson(lesson),
            break_loop=False
        )

    async def _complete_lesson(self):
        """Mark a lesson as completed"""
        agent_id = self.args.get("agent_id", self.agent_id)
        module_id = self.args.get("module_id")
        lesson_id = self.args.get("lesson_id")
        score = self.args.get("score", 100)

        # Track completion
        import json
        from datetime import datetime

        conn = self.manager.db._get_conn()
        cursor = conn.cursor()

        # Get or create learning progress
        cursor.execute("""
            SELECT * FROM learning_progress
            WHERE agent_id = ? AND path_id = ?
        """, (agent_id, f"module_{module_id}"))

        row = cursor.fetchone()
        if row:
            completed = json.loads(row['modules_completed'])
            if lesson_id not in completed:
                completed.append(lesson_id)
                cursor.execute("""
                    UPDATE learning_progress
                    SET modules_completed = ?, last_activity = ?
                    WHERE agent_id = ? AND path_id = ?
                """, (json.dumps(completed), datetime.now().isoformat(), agent_id, f"module_{module_id}"))
        else:
            cursor.execute("""
                INSERT INTO learning_progress (agent_id, path_id, modules_completed, last_activity)
                VALUES (?, ?, ?, ?)
            """, (agent_id, f"module_{module_id}", json.dumps([lesson_id]), datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Track skill progress for skills taught in module
        cursor = self.manager.db._get_conn().cursor()
        cursor.execute("SELECT skills_taught FROM training_modules WHERE module_id = ?", (module_id,))
        row = cursor.fetchone()
        if row:
            skills = json.loads(row['skills_taught'])
            for skill_id in skills:
                self.manager.track_skill_usage(
                    agent_id=agent_id,
                    skill_id=skill_id,
                    success=True,
                    assessment_score=score
                )

        return Response(
            message=f"## Lesson Completed\n\n**Lesson:** {lesson_id}\n**Module:** {module_id}\n**Score:** {score}%",
            break_loop=False
        )

    # ========== Learning Paths ==========

    async def _create_path(self):
        """Create a learning path"""
        result = self.manager.create_learning_path(
            path_id=self.args.get("path_id"),
            name=self.args.get("name"),
            target_role=self.args.get("target_role", "generalist"),
            description=self.args.get("description"),
            modules=self.args.get("modules", []),
            estimated_hours=self.args.get("estimated_hours"),
            certification=self.args.get("certification")
        )
        return Response(
            message=self._format_result(result, "Create Learning Path"),
            break_loop=False
        )

    async def _list_paths(self):
        """List available learning paths"""
        result = self.manager.list_learning_paths(
            target_role=self.args.get("target_role")
        )
        return Response(
            message=self._format_paths_list(result),
            break_loop=False
        )

    async def _get_path(self):
        """Get learning path details"""
        result = self.manager.get_learning_path(
            path_id=self.args.get("path_id")
        )
        return Response(
            message=self._format_path_details(result),
            break_loop=False
        )

    async def _enroll_path(self):
        """Enroll agent in a learning path"""
        agent_id = self.args.get("agent_id", self.agent_id)
        path_id = self.args.get("path_id")

        from datetime import datetime
        import json

        conn = self.manager.db._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO learning_progress (agent_id, path_id, current_module_id, started_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(agent_id, path_id) DO UPDATE SET
                last_activity = excluded.started_at
        """, (agent_id, path_id, None, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return Response(
            message=f"## Enrolled in Learning Path\n\n**Agent:** {agent_id}\n**Path:** {path_id}",
            break_loop=False
        )

    async def _get_progress(self):
        """Get learning progress for an agent"""
        agent_id = self.args.get("agent_id", self.agent_id)
        path_id = self.args.get("path_id")

        import json
        conn = self.manager.db._get_conn()
        cursor = conn.cursor()

        if path_id:
            cursor.execute("""
                SELECT lp.*, p.name as path_name, p.modules as path_modules
                FROM learning_progress lp
                LEFT JOIN learning_paths p ON lp.path_id = p.path_id
                WHERE lp.agent_id = ? AND lp.path_id = ?
            """, (agent_id, path_id))
        else:
            cursor.execute("""
                SELECT lp.*, p.name as path_name, p.modules as path_modules
                FROM learning_progress lp
                LEFT JOIN learning_paths p ON lp.path_id = p.path_id
                WHERE lp.agent_id = ?
            """, (agent_id,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            r['modules_completed'] = json.loads(r['modules_completed']) if r['modules_completed'] else []
            r['path_modules'] = json.loads(r['path_modules']) if r['path_modules'] else []
            results.append(r)

        return Response(
            message=self._format_learning_progress(results),
            break_loop=False
        )

    # ========== Practice & Assessment ==========

    async def _practice_task(self):
        """Generate a practice task for a skill"""
        skill_id = self.args.get("skill_id")
        skill = self.manager.get_skill(skill_id)

        if "error" in skill:
            return Response(message=f"Skill not found: {skill_id}", break_loop=False)

        # Generate practice based on skill level
        agent_skills = self.manager.get_agent_skills(self.agent_id)
        current_level = 1
        for s in agent_skills:
            if s['skill_id'] == skill_id:
                current_level = s['current_level']
                break

        practice = self._generate_practice(skill, current_level)

        return Response(
            message=self._format_practice(practice),
            break_loop=False
        )

    def _generate_practice(self, skill: dict, level: int) -> dict:
        """Generate practice task based on skill and level"""
        related_tools = skill.get('related_tools', [])

        practice_templates = {
            1: {
                "type": "guided",
                "prompt": f"Follow the step-by-step guide to practice {skill['name']}",
                "hints_enabled": True
            },
            2: {
                "type": "structured",
                "prompt": f"Complete the following task using {skill['name']} concepts",
                "hints_enabled": True
            },
            3: {
                "type": "independent",
                "prompt": f"Solve this problem applying {skill['name']}",
                "hints_enabled": False
            },
            4: {
                "type": "optimization",
                "prompt": f"Improve the given solution using advanced {skill['name']} techniques",
                "hints_enabled": False
            },
            5: {
                "type": "teaching",
                "prompt": f"Create an example that demonstrates {skill['name']} to others",
                "hints_enabled": False
            }
        }

        template = practice_templates.get(level, practice_templates[1])
        return {
            "skill_id": skill['skill_id'],
            "skill_name": skill['name'],
            "level": level,
            "tools": related_tools,
            **template
        }

    async def _take_assessment(self):
        """Take a skill assessment"""
        skill_id = self.args.get("skill_id")
        answers = self.args.get("answers", [])

        # Get skill assessment questions (if defined)
        skill = self.manager.get_skill(skill_id)
        if "error" in skill:
            return Response(message=f"Skill not found: {skill_id}", break_loop=False)

        # Calculate score
        score = self.args.get("score", 80)  # Default or provided score

        # Track assessment
        result = self.manager.track_skill_usage(
            agent_id=self.agent_id,
            skill_id=skill_id,
            success=score >= 70,
            assessment_score=score
        )

        return Response(
            message=self._format_assessment_result(result, score),
            break_loop=False
        )

    async def _get_recommendations(self):
        """Get skill recommendations for an agent"""
        agent_id = self.args.get("agent_id", self.agent_id)
        target_role = self.args.get("target_role")

        # Get current skills
        current_skills = self.manager.get_agent_skills(agent_id)
        current_skill_ids = {s['skill_id'] for s in current_skills}
        current_levels = {s['skill_id']: s['current_level'] for s in current_skills}

        # Get all skills
        all_skills = self.manager.list_skills()

        recommendations = []

        for skill in all_skills:
            skill_id = skill['skill_id']

            # Check prerequisites met
            prereqs = skill.get('prerequisites', [])
            prereqs_met = all(
                current_levels.get(p.get('skill_id'), 0) >= p.get('min_level', 1)
                for p in prereqs
            )

            if skill_id not in current_skill_ids:
                if prereqs_met:
                    recommendations.append({
                        "skill_id": skill_id,
                        "name": skill['name'],
                        "category": skill['category'],
                        "reason": "Prerequisites met, ready to learn",
                        "priority": "high" if not prereqs else "medium"
                    })
            elif current_levels.get(skill_id, 1) < 5:
                recommendations.append({
                    "skill_id": skill_id,
                    "name": skill['name'],
                    "category": skill['category'],
                    "current_level": current_levels[skill_id],
                    "reason": f"Level up from {current_levels[skill_id]} to {current_levels[skill_id] + 1}",
                    "priority": "medium"
                })

        return Response(
            message=self._format_recommendations(recommendations),
            break_loop=False
        )

    # ========== Reporting ==========

    async def _skill_report(self):
        """Generate skill proficiency report"""
        agent_id = self.args.get("agent_id", self.agent_id)
        skills = self.manager.get_agent_skills(agent_id)

        # Calculate summary stats
        total_skills = len(skills)
        avg_level = sum(s['current_level'] for s in skills) / total_skills if total_skills else 0
        total_completions = sum(s['completions'] for s in skills)

        by_category = {}
        for s in skills:
            cat = s.get('category', 'uncategorized')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(s)

        return Response(
            message=self._format_skill_report(skills, {
                "total_skills": total_skills,
                "avg_level": round(avg_level, 1),
                "total_completions": total_completions,
                "by_category": by_category
            }),
            break_loop=False
        )

    async def _training_dashboard(self):
        """Get training dashboard overview"""
        agent_id = self.args.get("agent_id", self.agent_id)

        skills = self.manager.get_agent_skills(agent_id)
        paths = self.manager.list_learning_paths()
        stats = self.manager.get_stats()

        # Get learning progress
        import json
        conn = self.manager.db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM learning_progress WHERE agent_id = ?", (agent_id,))
        progress = [dict(row) for row in cursor.fetchall()]
        for p in progress:
            p['modules_completed'] = json.loads(p['modules_completed']) if p['modules_completed'] else []
        conn.close()

        return Response(
            message=self._format_dashboard(skills, paths, progress, stats),
            break_loop=False
        )

    # ========== Formatting Helpers ==========

    def _format_result(self, result: dict, title: str) -> str:
        if "error" in result:
            return f"## {title}\n\n**Error:** {result['error']}"
        lines = [f"## {title}\n"]
        for key, value in result.items():
            lines.append(f"**{key}:** {value}")
        return "\n".join(lines)

    def _format_skill_result(self, result: dict) -> str:
        if "error" in result:
            return f"**Error:** {result['error']}"
        return f"""## Skill Registered

**Skill ID:** {result['skill_id']}
**Name:** {result['name']}
**Category:** {result['category']}
**Status:** {result['status']}"""

    def _format_skill_details(self, skill: dict) -> str:
        if "error" in skill:
            return f"**Error:** {skill['error']}"

        levels = skill.get('proficiency_levels', [])
        level_lines = []
        for lvl in levels:
            criteria = ", ".join(lvl.get('criteria', []))
            level_lines.append(f"  {lvl['level']}. **{lvl['name']}**: {criteria}")

        prereqs = skill.get('prerequisites', [])
        prereq_lines = [f"  - {p['skill_id']} (level {p.get('min_level', 1)})" for p in prereqs]

        tools = skill.get('related_tools', [])

        return f"""## Skill: {skill['name']}

**ID:** {skill['skill_id']}
**Category:** {skill['category']}
**Description:** {skill.get('description', 'N/A')}

### Proficiency Levels
{chr(10).join(level_lines)}

### Prerequisites
{chr(10).join(prereq_lines) if prereq_lines else '  None'}

### Related Tools
{', '.join(tools) if tools else 'None'}"""

    def _format_skills_list(self, skills: list) -> str:
        if not skills:
            return "## Skills\n\nNo skills defined yet."

        lines = ["## Available Skills\n"]
        lines.append("| Skill ID | Name | Category |")
        lines.append("|----------|------|----------|")

        for s in skills:
            lines.append(f"| {s['skill_id']} | {s['name']} | {s['category']} |")

        lines.append(f"\n*Total: {len(skills)} skills*")
        return "\n".join(lines)

    def _format_proficiency(self, skills: list) -> str:
        if not skills:
            return "## Skill Proficiency\n\nNo skills tracked yet."

        lines = ["## Skill Proficiency\n"]

        for s in skills:
            level = s['current_level']
            name = s.get('name', s['skill_id'])
            completions = s['completions']

            bar = "★" * level + "☆" * (5 - level)
            lines.append(f"**{name}** [{bar}] Level {level}")
            lines.append(f"  Completions: {completions} | Last: {s.get('last_practiced', 'Never')[:10]}")
            lines.append("")

        return "\n".join(lines)

    def _format_assessment_result(self, result: dict, score: float = None) -> str:
        if "error" in result:
            return f"**Error:** {result['error']}"

        if result.get('status') == 'level_up':
            return f"""## Level Up! 🎉

**Skill:** {result['skill_id']}
**New Level:** {result['new_level']} ({result['level_name']})
**Score:** {score}%""" if score else f"""## Level Up! 🎉

**Skill:** {result['skill_id']}
**New Level:** {result['new_level']} ({result['level_name']})"""

        return f"""## Skill Practice Recorded

**Skill:** {result['skill_id']}
**Success:** {result['success']}
{f'**Score:** {score}%' if score else ''}"""

    def _format_module(self, module: dict) -> str:
        lessons = module.get('lessons', [])
        lesson_lines = []
        for i, l in enumerate(lessons, 1):
            lesson_lines.append(f"  {i}. {l.get('name', l.get('id'))} ({l.get('type', 'lesson')})")

        return f"""## Training Module: {module['name']}

**ID:** {module['module_id']}
**Description:** {module.get('description', 'N/A')}
**Target Level:** {module.get('skill_level_target', 'N/A')}
**Skills Taught:** {', '.join(module.get('skills_taught', []))}

### Lessons
{chr(10).join(lesson_lines) if lesson_lines else '  No lessons defined'}"""

    def _format_lesson(self, lesson: dict) -> str:
        content = lesson.get('content', {})
        objectives = content.get('objectives', [])
        steps = content.get('steps', [])

        obj_lines = [f"  - {o}" for o in objectives]
        step_lines = []
        for i, s in enumerate(steps, 1):
            step_lines.append(f"  {i}. {s.get('instruction', 'Step')}")
            if s.get('action'):
                step_lines.append(f"     Action: `{s['action']}`")

        return f"""## Lesson: {lesson['name']}

**Type:** {lesson.get('type', 'lesson')}
**Duration:** {lesson.get('duration_minutes', 'N/A')} minutes

### Objectives
{chr(10).join(obj_lines) if obj_lines else '  Not specified'}

### Introduction
{content.get('introduction', 'Begin the lesson.')}

### Steps
{chr(10).join(step_lines) if step_lines else '  Follow the lesson content.'}

### Key Points
{chr(10).join(['  - ' + k for k in content.get('key_points', [])])}"""

    def _format_paths_list(self, paths: list) -> str:
        if not paths:
            return "## Learning Paths\n\nNo learning paths defined yet."

        lines = ["## Learning Paths\n"]
        lines.append("| Path ID | Name | Target Role | Hours |")
        lines.append("|---------|------|-------------|-------|")

        for p in paths:
            hours = p.get('estimated_hours', 'N/A')
            lines.append(f"| {p['path_id']} | {p['name']} | {p.get('target_role', 'all')} | {hours} |")

        return "\n".join(lines)

    def _format_path_details(self, path: dict) -> str:
        if "error" in path:
            return f"**Error:** {path['error']}"

        modules = path.get('modules', [])
        module_lines = []
        for m in modules:
            req = "Required" if m.get('required', True) else "Optional"
            prereqs = m.get('prerequisites', [])
            module_lines.append(f"  - {m['module_id']} ({req})")
            if prereqs:
                module_lines.append(f"    Prerequisites: {', '.join(prereqs)}")

        cert = path.get('certification')
        cert_info = ""
        if cert:
            cert_info = f"""
### Certification: {cert.get('name', 'Available')}
Requirements:
  - Min modules: {cert.get('requirements', {}).get('min_modules_completed', 'All')}
  - Min score: {cert.get('requirements', {}).get('min_overall_score', 70)}%"""

        return f"""## Learning Path: {path['name']}

**ID:** {path['path_id']}
**Target Role:** {path.get('target_role', 'all')}
**Description:** {path.get('description', 'N/A')}
**Estimated Hours:** {path.get('estimated_hours', 'N/A')}

### Modules
{chr(10).join(module_lines) if module_lines else '  No modules defined'}
{cert_info}"""

    def _format_learning_progress(self, progress: list) -> str:
        if not progress:
            return "## Learning Progress\n\nNot enrolled in any learning paths."

        lines = ["## Learning Progress\n"]

        for p in progress:
            completed = len(p.get('modules_completed', []))
            total = len(p.get('path_modules', [])) or 'N/A'
            pct = (completed / total * 100) if isinstance(total, int) and total > 0 else 0

            bar_filled = int(pct / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)

            lines.append(f"### {p.get('path_name', p['path_id'])}")
            lines.append(f"[{bar}] {pct:.0f}%")
            lines.append(f"Completed: {completed}/{total} modules")
            lines.append(f"Started: {p.get('started_at', 'N/A')[:10]}")
            lines.append("")

        return "\n".join(lines)

    def _format_practice(self, practice: dict) -> str:
        return f"""## Practice Task: {practice['skill_name']}

**Skill Level:** {practice['level']}
**Type:** {practice['type']}

### Task
{practice['prompt']}

### Tools Available
{', '.join(practice.get('tools', [])) or 'Any'}

### Hints
{'Enabled - ask for hints if needed' if practice.get('hints_enabled') else 'Disabled at this level'}

*Complete this task and use `assess_skill` to record your result.*"""

    def _format_recommendations(self, recommendations: list) -> str:
        if not recommendations:
            return "## Skill Recommendations\n\nNo new recommendations. You're doing great!"

        lines = ["## Skill Recommendations\n"]

        high = [r for r in recommendations if r.get('priority') == 'high']
        medium = [r for r in recommendations if r.get('priority') == 'medium']

        if high:
            lines.append("### High Priority")
            for r in high:
                lines.append(f"- **{r['name']}** ({r['category']}): {r['reason']}")
            lines.append("")

        if medium:
            lines.append("### Suggested")
            for r in medium[:5]:
                level = r.get('current_level', '')
                lines.append(f"- **{r['name']}** {f'[Level {level}]' if level else ''}: {r['reason']}")

        return "\n".join(lines)

    def _format_skill_report(self, skills: list, summary: dict) -> str:
        lines = [
            "## Skill Proficiency Report\n",
            f"**Total Skills:** {summary['total_skills']}",
            f"**Average Level:** {summary['avg_level']}",
            f"**Total Practice Completions:** {summary['total_completions']}",
            ""
        ]

        for category, cat_skills in summary['by_category'].items():
            lines.append(f"### {category.title()}")
            for s in cat_skills:
                level = s['current_level']
                bar = "★" * level + "☆" * (5 - level)
                lines.append(f"- {s.get('name', s['skill_id'])} [{bar}]")
            lines.append("")

        return "\n".join(lines)

    def _format_dashboard(self, skills: list, paths: list, progress: list, stats: dict) -> str:
        skill_count = len(skills)
        avg_level = sum(s['current_level'] for s in skills) / skill_count if skill_count else 0
        enrolled = len(progress)

        return f"""## Training Dashboard

### Overview
- **Skills Tracked:** {skill_count}
- **Average Proficiency:** {avg_level:.1f}/5
- **Learning Paths Enrolled:** {enrolled}
- **Available Paths:** {len(paths)}

### Quick Stats
- Total Skills Available: {stats.get('total_skills', 0)}
- Learning Paths Available: {stats.get('total_learning_paths', 0)}
- Total Workflows: {stats.get('total_workflows', 0)}

### Top Skills
{chr(10).join([f"- {s.get('name', s['skill_id'])}: Level {s['current_level']}" for s in sorted(skills, key=lambda x: -x['current_level'])[:5]]) if skills else '  None yet'}

### Active Learning
{chr(10).join([f"- {p.get('path_name', p['path_id'])}: {len(p.get('modules_completed', []))} modules completed" for p in progress[:3]]) if progress else '  Not enrolled in any paths'}"""

    def _format_help(self) -> str:
        return """## Workflow Training Tool

Manage skill development, training modules, and learning progressions.

### Skill Management
- `define_skill` - Define a new skill with proficiency levels
- `get_skill` - Get skill details
- `list_skills` - List all available skills
- `assess_skill` - Record skill assessment/practice
- `get_proficiency` - Get agent's skill levels

### Training Modules
- `create_module` - Create a training module with lessons
- `get_module` - Get module details
- `start_lesson` - Start a lesson
- `complete_lesson` - Mark lesson as completed

### Learning Paths
- `create_path` - Create a learning path
- `list_paths` - List available paths
- `get_path` - Get path details
- `enroll_path` - Enroll in a learning path
- `get_progress` - Get learning progress

### Practice & Assessment
- `practice_task` - Generate practice task for a skill
- `take_assessment` - Take a skill assessment
- `get_recommendations` - Get skill recommendations

### Reporting
- `skill_report` - Generate skill proficiency report
- `training_dashboard` - Get training overview
"""
