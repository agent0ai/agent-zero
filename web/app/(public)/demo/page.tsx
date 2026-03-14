'use client'

import { useState } from 'react'

export default function DemoPage() {
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    company: '',
    email: '',
    industry: '',
    teamSize: '',
    painPoints: [] as string[],
    cloudPlatforms: [] as string[],
    governanceSteps: '',
    integrations: [] as string[],
    useCase: '',
    complexity: '',
    budget: '',
    timeline: '',
  })

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleMultiSelectChange = (field: string, value: string) => {
    setFormData(prev => {
      const currentArray = prev[field as keyof typeof prev] as string[]
      return {
        ...prev,
        [field]: currentArray.includes(value)
          ? currentArray.filter(item => item !== value)
          : [...currentArray, value],
      }
    })
  }

  const handlePainPointChange = (point: string) => {
    handleMultiSelectChange('painPoints', point)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch('/api/demo-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        setSubmitted(true)
      } else {
        alert('Error submitting form. Please try again.')
      }
    } catch (error) {
      console.error('Form submission error:', error)
      alert('Error submitting form. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
        <main className="max-w-4xl mx-auto px-4 py-20 text-center">
          <h1 className="text-4xl font-bold text-white mb-6">
            Thank You! Your Demo Request Has Been Received
          </h1>
          <p className="text-xl text-slate-300 mb-8">
            Our team will reach out within 24 hours to schedule your personalized demo and discuss
            how Agent Jumbo can solve your specific use case.
          </p>
          <div className="bg-slate-800 rounded-lg p-8 mb-8 border border-slate-700">
            <p className="text-slate-300 mb-4">
              <strong>What happens next:</strong>
            </p>
            <ul className="text-left text-slate-300 space-y-2 max-w-2xl mx-auto">
              <li>&#10003; Our team reviews your requirements</li>
              <li>&#10003; We customize a demo for your use case</li>
              <li>&#10003; Schedule a 30-min personalized walkthrough</li>
              <li>&#10003; Discuss integration with your systems</li>
              <li>&#10003; Answer any questions about pricing and implementation</li>
            </ul>
          </div>
          <a
            href="/"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg transition"
          >
            Back to Home
          </a>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      <main className="max-w-2xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            Get a Custom Demo
          </h1>
          <p className="text-lg text-slate-300">
            See how Agent Jumbo can solve your specific AI workflow challenges.
            Fill out the form below and our team will reach out within 24 hours.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-slate-800 rounded-lg p-8 space-y-6 border border-slate-700">

          {/* Company & Email */}
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white font-semibold mb-2">
                Company Name *
              </label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
                required
                className="w-full px-4 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                placeholder="Your company"
              />
            </div>
            <div>
              <label className="block text-white font-semibold mb-2">
                Email *
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                required
                className="w-full px-4 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
                placeholder="your@email.com"
              />
            </div>
          </div>

          {/* Industry & Team Size */}
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white font-semibold mb-2">
                Industry *
              </label>
              <select
                value={formData.industry}
                onChange={(e) => handleInputChange('industry', e.target.value)}
                required
                className="w-full px-4 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Select an industry</option>
                <option value="finance">Finance / Banking</option>
                <option value="healthcare">Healthcare</option>
                <option value="retail">Retail / E-commerce</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="technology">Technology</option>
                <option value="insurance">Insurance</option>
                <option value="operations">Operations / Business Services</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-white font-semibold mb-2">
                Team Size *
              </label>
              <select
                value={formData.teamSize}
                onChange={(e) => handleInputChange('teamSize', e.target.value)}
                required
                className="w-full px-4 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Select team size</option>
                <option value="1-50">1-50 employees</option>
                <option value="50-500">50-500 employees</option>
                <option value="500-5000">500-5,000 employees</option>
                <option value="5000+">5,000+ employees</option>
              </select>
            </div>
          </div>

          {/* Cloud Platforms */}
          <div>
            <label className="block text-white font-semibold mb-3">
              Which cloud platforms do you use? (Select all that apply)
            </label>
            <div className="space-y-2 bg-slate-700 rounded p-4">
              {[
                { value: 'kubernetes', label: 'Kubernetes' },
                { value: 'aws', label: 'AWS' },
                { value: 'gcp', label: 'Google Cloud Platform' },
                { value: 'azure', label: 'Azure' },
                { value: 'multiple', label: 'Multiple clouds' },
                { value: 'onprem', label: 'On-premises only' },
              ].map(({ value, label }) => (
                <label key={value} className="flex items-center text-slate-200 cursor-pointer hover:text-white">
                  <input
                    type="checkbox"
                    checked={formData.cloudPlatforms.includes(value)}
                    onChange={() => handleMultiSelectChange('cloudPlatforms', value)}
                    className="mr-3 w-4 h-4 accent-blue-600"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* Governance Steps */}
          <div>
            <label className="block text-white font-semibold mb-3">
              How many approval steps for production changes? *
            </label>
            <div className="space-y-2 bg-slate-700 rounded p-4">
              {[
                { value: 'none', label: 'None (move fast)' },
                { value: '1-2', label: '1-2 steps' },
                { value: '3+', label: '3+ steps (strict compliance)' },
              ].map(({ value, label }) => (
                <label key={value} className="flex items-center text-slate-200 cursor-pointer hover:text-white">
                  <input
                    type="radio"
                    name="governanceSteps"
                    value={value}
                    checked={formData.governanceSteps === value}
                    onChange={(e) => handleInputChange('governanceSteps', e.target.value)}
                    className="mr-3 w-4 h-4 accent-blue-600"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* Integrations */}
          <div>
            <label className="block text-white font-semibold mb-3">
              What systems do you integrate with? (Select all that apply)
            </label>
            <div className="space-y-2 bg-slate-700 rounded p-4">
              {[
                { value: 'github', label: 'Jira / GitHub / GitLab' },
                { value: 'kubernetes-docker', label: 'Kubernetes / Docker' },
                { value: 'cloud-services', label: 'AWS / GCP / Azure' },
                { value: 'communication', label: 'Slack / Teams / Email' },
                { value: 'crm', label: 'Salesforce / CRM' },
                { value: 'pms', label: 'PMS (Hostaway, Lodgify, etc.)' },
                { value: 'finance', label: 'Finance systems' },
              ].map(({ value, label }) => (
                <label key={value} className="flex items-center text-slate-200 cursor-pointer hover:text-white">
                  <input
                    type="checkbox"
                    checked={formData.integrations.includes(value)}
                    onChange={() => handleMultiSelectChange('integrations', value)}
                    className="mr-3 w-4 h-4 accent-blue-600"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* Primary Use Case */}
          <div>
            <label className="block text-white font-semibold mb-3">
              What&apos;s your primary need? *
            </label>
            <div className="space-y-2 bg-slate-700 rounded p-4">
              {[
                { value: 'multi-cloud', label: 'Deploy to multiple clouds' },
                { value: 'approvals', label: 'Enterprise approval workflows' },
                { value: 'costs', label: 'Track AI costs and usage' },
                { value: 'integration', label: 'Integrate with business systems' },
                { value: 'workflows', label: 'Build intelligent workflows' },
                { value: 'governance', label: 'Ensure compliance/governance' },
              ].map(({ value, label }) => (
                <label key={value} className="flex items-center text-slate-200 cursor-pointer hover:text-white">
                  <input
                    type="radio"
                    name="useCase"
                    value={value}
                    checked={formData.useCase === value}
                    onChange={(e) => handleInputChange('useCase', e.target.value)}
                    className="mr-3 w-4 h-4 accent-blue-600"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* Pain Points */}
          <div>
            <label className="block text-white font-semibold mb-3">
              What are your biggest challenges? (Select all that apply)
            </label>
            <div className="space-y-2 bg-slate-700 rounded p-4">
              {[
                { value: 'cost', label: 'LLM/AI costs are spiraling out of control' },
                { value: 'integration', label: 'Integrating AI with business systems' },
                { value: 'monitoring', label: 'Monitoring and debugging AI in production' },
                { value: 'governance', label: 'Compliance and governance requirements' },
                { value: 'orchestration', label: 'Orchestrating complex workflows' },
                { value: 'speed', label: 'Speed to deploy AI-powered features' },
              ].map(({ value, label }) => (
                <label key={value} className="flex items-center text-slate-200 cursor-pointer hover:text-white">
                  <input
                    type="checkbox"
                    checked={formData.painPoints.includes(value)}
                    onChange={() => handlePainPointChange(value)}
                    className="mr-3 w-4 h-4 accent-blue-600"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* Workflow Complexity */}
          <div>
            <label className="block text-white font-semibold mb-3">
              Your AI Workflow Complexity *
            </label>
            <div className="space-y-2 bg-slate-700 rounded p-4">
              {['Simple', 'Medium', 'Complex'].map((option) => (
                <label key={option} className="flex items-center text-slate-200 cursor-pointer hover:text-white">
                  <input
                    type="radio"
                    name="complexity"
                    value={option}
                    checked={formData.complexity === option}
                    onChange={(e) => handleInputChange('complexity', e.target.value)}
                    required
                    className="mr-3 w-4 h-4 accent-blue-600"
                  />
                  {option}
                </label>
              ))}
            </div>
          </div>

          {/* Budget & Timeline */}
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white font-semibold mb-2">
                Budget Range *
              </label>
              <select
                value={formData.budget}
                onChange={(e) => handleInputChange('budget', e.target.value)}
                required
                className="w-full px-4 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Select budget</option>
                <option value="50-100k">$50K-$100K</option>
                <option value="100-250k">$100K-$250K</option>
                <option value="250-500k">$250K-$500K</option>
                <option value="500k+">$500K+</option>
              </select>
            </div>
            <div>
              <label className="block text-white font-semibold mb-2">
                Timeline *
              </label>
              <select
                value={formData.timeline}
                onChange={(e) => handleInputChange('timeline', e.target.value)}
                required
                className="w-full px-4 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Select timeline</option>
                <option value="urgent">ASAP (Urgent)</option>
                <option value="month">Next 30 days</option>
                <option value="quarter">Next quarter (3-6 months)</option>
                <option value="year">This year (6-12 months)</option>
              </select>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 text-white font-bold py-3 px-4 rounded-lg transition"
          >
            {loading ? 'Submitting...' : 'Request Demo'}
          </button>

          <p className="text-center text-slate-400 text-sm">
            We respect your privacy. Your information will only be used to schedule your demo.
          </p>
        </form>
      </main>
    </div>
  )
}
