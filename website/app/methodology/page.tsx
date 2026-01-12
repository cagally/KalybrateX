import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Methodology - How We Rate AI Skills | KalybrateX',
  description:
    'Learn how KalybrateX rates AI agent skills using A/B comparison testing, security analysis, and cost estimation.',
};

export default function MethodologyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
        How We Rate Skills
      </h1>

      {/* Quick Summary */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 mb-12 border border-blue-200 dark:border-blue-800">
        <p className="text-lg text-blue-800 dark:text-blue-200">
          <strong>TL;DR:</strong> We run the same prompts with and without the skill, then have an
          AI judge which response is better. Skills that consistently produce better responses get
          higher grades.
        </p>
      </div>

      {/* The Process */}
      <section className="mb-12">
        <h2 id="process" className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          The A/B Testing Process
        </h2>

        <div className="space-y-8">
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
              1
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Generate Test Prompts
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                We analyze each SKILL.md and generate 10 prompts that would naturally use the
                skill&apos;s capabilities. Prompts vary from simple to complex.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
              2
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Run A/B Comparisons
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                For each prompt, we get two responses: one from Claude <strong>without</strong> the
                skill (baseline), and one <strong>with</strong> the SKILL.md in the system prompt.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
              3
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Judge the Results
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Claude Sonnet judges which response is better. To avoid position bias, we randomize
                whether the skill response is shown first or second.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
              4
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Calculate Score</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Win Rate = (Skill Wins) / (Skill Wins + Baseline Wins). Ties don&apos;t count.
                Higher win rate = better skill.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Grading Scale */}
      <section className="mb-12">
        <h2 id="grades" className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          What the Grades Mean
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Grade
                </th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Win Rate
                </th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                  Meaning
                </th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-3 px-4">
                  <span className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold">
                    A
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-700 dark:text-gray-300">80%+</td>
                <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                  Excellent. Significantly improves responses.
                </td>
              </tr>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-3 px-4">
                  <span className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
                    B
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-700 dark:text-gray-300">60-79%</td>
                <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                  Good. Usually improves responses.
                </td>
              </tr>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-3 px-4">
                  <span className="w-8 h-8 rounded-full bg-yellow-500 text-white flex items-center justify-center font-bold">
                    C
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-700 dark:text-gray-300">40-59%</td>
                <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                  Mixed. About as good as no skill.
                </td>
              </tr>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-3 px-4">
                  <span className="w-8 h-8 rounded-full bg-orange-500 text-white flex items-center justify-center font-bold">
                    D
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-700 dark:text-gray-300">20-39%</td>
                <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                  Poor. Often makes responses worse.
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4">
                  <span className="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center font-bold">
                    F
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-700 dark:text-gray-300">&lt;20%</td>
                <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                  Fail. Almost always makes responses worse.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Security */}
      <section className="mb-12">
        <h2 id="security" className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Security Checking
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          We analyze each SKILL.md for potential security risks:
        </p>

        <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400 mb-6">
          <li>
            <strong>Data exfiltration</strong> - Could send your data to external servers
          </li>
          <li>
            <strong>File system abuse</strong> - Could access or modify files it shouldn&apos;t
          </li>
          <li>
            <strong>Credential theft</strong> - Could expose API keys or passwords
          </li>
          <li>
            <strong>Code injection</strong> - Could execute arbitrary code
          </li>
          <li>
            <strong>Malicious dependencies</strong> - Could install harmful packages
          </li>
        </ul>

        <div className="grid sm:grid-cols-3 gap-4">
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <p className="font-medium text-green-800 dark:text-green-200">✓ Secure</p>
            <p className="text-sm text-green-700 dark:text-green-300">No issues found</p>
          </div>
          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
            <p className="font-medium text-orange-800 dark:text-orange-200">⚠ Warning</p>
            <p className="text-sm text-orange-700 dark:text-orange-300">Minor concerns found</p>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-200 dark:border-red-800">
            <p className="font-medium text-red-800 dark:text-red-200">✗ Fail</p>
            <p className="text-sm text-red-700 dark:text-red-300">Serious security risks</p>
          </div>
        </div>
      </section>

      {/* Cost */}
      <section className="mb-12">
        <h2 id="cost" className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Cost Estimation
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          We estimate the cost per use based on the average output tokens generated when using the
          skill. This uses Claude Haiku pricing ($1.25 per 1M output tokens).
        </p>

        <p className="text-gray-600 dark:text-gray-400">
          Skills that produce longer responses cost more. We also show the baseline cost (without
          skill) so you can compare.
        </p>
      </section>

      {/* FAQ */}
      <section className="mb-12">
        <h2 id="faq" className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Frequently Asked Questions
        </h2>

        <div className="space-y-6">
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Why A/B testing instead of benchmarks?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Traditional benchmarks test specific capabilities. We want to answer a simpler
              question: &quot;Does this skill make Claude better at the task it claims to help
              with?&quot; A/B testing answers that directly.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Isn&apos;t having AI judge AI responses biased?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              We randomize which response is shown first to avoid position bias. We also show the
              full evidence (both responses + reasoning) so you can verify the judgments yourself.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              How often are skills re-evaluated?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Currently, skills are evaluated once. We plan to add periodic re-evaluation to track
              changes over time.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Can I submit a skill for rating?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Yes! Use the &quot;Submit a skill&quot; button in the footer to request a rating for
              your skill.
            </p>
          </div>
        </div>
      </section>

      {/* Back to leaderboard */}
      <div className="pt-8 border-t border-gray-200 dark:border-gray-700">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline"
        >
          ← Back to Leaderboard
        </Link>
      </div>
    </div>
  );
}
