# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Generates reports base on bisect result data."""

import copy

_CONFIDENCE_THRESHOLD = 99.5

_BISECT_REPORT_TEMPLATE = """
===== BISECT JOB RESULTS =====
Status: %(status)s

%(result)s

Bisect job ran on: %(bisect_bot)s
Bug ID: %(bug_id)s

Test Command: %(command)s
Test Metric: %(metric)s
Relative Change: %(change)s
Score: %(score)s

Buildbot stdio: %(buildbot_log_url)s
Job details: %(issue_url)s

"""

_RESULTS_REVISION_INFO = """
===== SUSPECTED CL(s) =====
Subject : %(subject)s
Author  : %(author)s
Commit description:
  %(commit_info)s
Commit  : %(cl)s
Date    : %(cl_date)s

"""

_ABORTED_REASON_TEMPLATE = """
=== Bisection aborted ===
The bisect was aborted because %s
Please contact the the team (see below) if you believe this is in error.
"""

_WARNINGS_TEMPLATE = """
=== Warnings ===
The following warnings were raised by the bisect job:

 * %s
"""

_REVISION_TABLE_TEMPLATE = """
===== TESTED REVISIONS =====
%(table)s"""

_RESULTS_THANKYOU = """
| O O | Visit http://www.chromium.org/developers/speed-infra/perf-bug-faq
|  X  | for more information addressing perf regression bugs. For feedback,
| / \\ | file a bug with label Cr-Tests-AutoBisect.  Thank you!"""


def GetReport(try_job_entity):
  """Generates a report for bisect results.

  This was ported from recipe_modules/auto_bisect/bisect_results.py.

  Args:
    try_job_entity: A TryJob entity.

  Returns:
    Bisect report string.
  """
  results_data = copy.deepcopy(try_job_entity.results_data)
  if not results_data:
    return ''
  result = ''
  if results_data.get('aborted_reason'):
    result += _ABORTED_REASON_TEMPLATE % results_data['aborted_reason']

  if results_data.get('warnings'):
    warnings = '\n'.join(results_data['warnings'])
    result += _WARNINGS_TEMPLATE % warnings

  if results_data.get('culprit_data'):
    result += _RESULTS_REVISION_INFO % results_data['culprit_data']

  if results_data.get('revision_data'):
    result += _RevisionTable(results_data)

  results_data['result'] = result
  report = _BISECT_REPORT_TEMPLATE % results_data
  report += _RESULTS_THANKYOU
  return report


def _MakeLegacyRevisionString(r):
  result = 'chromium@' + str(r.get('commit_pos', 'unknown'))
  if r.get('depot_name', 'chromium') != 'chromium':
    result += ',%s@%s' % (r['depot_name'], r.get('deps_revision', 'unknown'))
  return result


def _RevisionTable(results_data):
  is_return_code = results_data.get('test_type') == 'return_code'
  has_culprit = 'culprit_data' in results_data

  def RevisionRow(r):
    result = [
        r.get('revision_string', _MakeLegacyRevisionString(r)),
        _FormatNumber(r['mean_value']),
        _FormatNumber(r['std_dev']),
        len(r['values']),
        r['result'],
        '<-' if has_culprit == r else '',
    ]
    return map(str, result)
  revision_rows = [RevisionRow(r) for r in results_data['revision_data']]

  headers_row = [[
      'Revision',
      'Mean Value' if not is_return_code else 'Exit Code',
      'Std. Dev.',
      'Num Values',
      'Good?',
      '',
  ]]
  all_rows = headers_row + revision_rows
  return _REVISION_TABLE_TEMPLATE % {'table': _PrettyTable(all_rows)}


def _FormatNumber(x):
  if x is None:
    return 'N/A'
  if isinstance(x, int):
    return str(x)
  return str(round(x, 6))


def _PrettyTable(data):
  results = []
  for row in data:
    results.append(
        (('%-24s' + '%-12s' * (len(row) - 1)) % tuple(row)).rstrip())
  return '\n'.join(results)
