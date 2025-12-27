# Example: Component Library Creation

## User Request

"Build a reusable Button component library with multiple variants and sizes"

## Agent Workflow

### Step 1: Generate Base Button

```json
{
  "tool_name": "component_generator",
  "tool_args": {
    "name": "Button",
    "props": [
      {"name": "variant", "type": "'default' | 'outline' | 'ghost'", "required": false},
      {"name": "size", "type": "'sm' | 'md' | 'lg'", "required": false},
      {"name": "children", "type": "React.ReactNode", "required": true},
      {"name": "onClick", "type": "() => void", "required": false}
    ],
    "features": ["accessibility", "responsive", "shadcn-ui"]
  }
}
```

### Step 2: Enhance with Variants

```json
{
  "tool_name": "quick_edit",
  "tool_args": {
    "file_path": "components/button.tsx",
    "edits": [
      {
        "operation": "insert_after",
        "marker": "export function Button",
        "insert": "\n  const variants = {\n    default: 'bg-primary text-white',\n    outline: 'border border-primary text-primary',\n    ghost: 'hover:bg-gray-100'\n  }"
      }
    ]
  }
}
```

## Result

Production-ready Button component with:
- Multiple variants (default, outline, ghost)
- Size options (sm, md, lg)
- Full TypeScript types
- Accessibility support
- shadcn/ui styling
