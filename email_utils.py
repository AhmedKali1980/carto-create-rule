# email_utils.py

import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_FROM, EMAIL_TO
import html
from collections import defaultdict
from users import get_users
from datetime import datetime


def extract_resource_name(event, is_iplist_event=False, iplist_href_to_bouquets=None):
    """
    Extracts the human-readable 'name' for the event resource for all major Illumio event types.
    For sec_policy.create, extracts all names under modified_objects.
    For IP list events, also returns the related BOUQUETS ruleset(s).
    """
    resource_name = "Unknown"
    bouquets_col = ""

    resource_changes = getattr(event, 'resource_changes', [])
    if not resource_changes:
        return resource_name, bouquets_col

    rc = resource_changes[0]
    resource = getattr(rc, 'resource', None)
    if resource is None:
        return resource_name, bouquets_col

    # Helper for both dict/object
    def get_resource_obj(res, key):
        if isinstance(res, dict):
            return res.get(key)
        else:
            return getattr(res, key, None)

    # Special case: sec_policy.create (multiple names in modified_objects)
    if get_resource_obj(resource, 'sec_policy'):
        sec_policy = get_resource_obj(resource, 'sec_policy')
        modified_objects = get_resource_obj(sec_policy, 'modified_objects')
        names = []
        if modified_objects and isinstance(modified_objects, dict):
            for obj_type, obj_dict in modified_objects.items():
                if isinstance(obj_dict, dict):
                    for item in obj_dict.values():
                        # For each object, get its 'name' if available
                        name = item.get('name') if isinstance(
                            item, dict) else None
                        if name:
                            names.append(name)
        if names:
            resource_name = ", ".join(names)
            return resource_name, bouquets_col

    # For sec_rule events: get ruleset name from sec_rule.rule_set.name
    if get_resource_obj(resource, 'sec_rule'):
        sec_rule = get_resource_obj(resource, 'sec_rule')
        rule_set = get_resource_obj(sec_rule, 'rule_set')
        if rule_set:
            name = get_resource_obj(rule_set, 'name')
            if name:
                resource_name = name
                return resource_name, bouquets_col

    # For rule_set events: get name from rule_set.name
    if get_resource_obj(resource, 'rule_set'):
        rule_set = get_resource_obj(resource, 'rule_set')
        name = get_resource_obj(rule_set, 'name')
        if name:
            resource_name = name
            return resource_name, bouquets_col
        # If not found, check for nested sec_rule.rule_set.name
        sec_rule = get_resource_obj(resource, 'sec_rule')
        if sec_rule:
            rule_set_nested = get_resource_obj(sec_rule, 'rule_set')
            if rule_set_nested:
                name_nested = get_resource_obj(rule_set_nested, 'name')
                if name_nested:
                    resource_name = name_nested
                    return resource_name, bouquets_col

    # For sec_policy_pending.delete: get name from rule_set.name
    if get_resource_obj(resource, 'rule_set'):
        rule_set = get_resource_obj(resource, 'rule_set')
        name = get_resource_obj(rule_set, 'name')
        if name:
            resource_name = name
            return resource_name, bouquets_col

    # For ip_list events: get name from ip_list.name
    if get_resource_obj(resource, 'ip_list'):
        ip_list = get_resource_obj(resource, 'ip_list')
        name = get_resource_obj(ip_list, 'name')
        href = get_resource_obj(ip_list, 'href')
        if name:
            resource_name = name
            if is_iplist_event and iplist_href_to_bouquets and href:
                bouquets_col = ", ".join(
                    sorted(iplist_href_to_bouquets.get(href, [])))
            return resource_name, bouquets_col

    # Fallback: try to find a name in any top-level resource key
    for key, res_obj in (resource.items() if isinstance(resource, dict) else []):
        if isinstance(res_obj, dict):
            name = res_obj.get('name')
            if name:
                resource_name = name
                break

    return resource_name, bouquets_col


def format_events_for_email_html(events, logger, iplist_href_to_bouquets):
    """
    Format events grouped by event_type into HTML tables with columns:
    Name | Event Created At | Event Created By | (plus BOUQUETS Ruleset(s) for IP list events)
    """
    if not events:
        logger.info("No relevant events detected in the last hour.")
        return "<p>No relevant events detected in the last hour.</p>"

    events_by_type = defaultdict(list)
    for event in events:
        event_type = getattr(event, 'event_type', 'Unknown')
        events_by_type[event_type].append(event)

    html_parts = []
    html_parts.append("<html><body>")
    html_parts.append("<h2>Illumio Policy Change Events</h2>")

    # Style for table
    html_parts.append("""
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            max-width: 800px;
            margin-bottom: 30px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: center;
        }
        th {
            background-color: #FF0000; color: white;
        }
        h3 {
            font-family: Arial, sans-serif;
            color: #333333;
        }
    </style>
    """)

    for event_type, ev_list in events_by_type.items():
        html_parts.append(f"<h3>Event: {html.escape(event_type)} </h3>")
        is_iplist_event = event_type.startswith('ip_list')
        if is_iplist_event:
            html_parts.append(
                "<table><thead><tr><th>Name</th><th>Event Created At</th><th>Event Created By</th><th>BOUQUETS Ruleset(s)</th></tr></thead><tbody>")
        else:
            html_parts.append(
                "<table><thead><tr><th>Name</th><th>Event Created At</th><th>Event Created By</th></tr></thead><tbody>")

        for event in ev_list:
            created_at = getattr(event, 'timestamp', 'Unknown')
            if created_at and len(created_at) >= 19:
                try:
                    c_at = created_at[:19]
                    c_at = datetime.strptime(c_at, "%Y-%m-%dT%H:%M:%S")
                    c_at = c_at.strftime("%B %d, %Y, %H:%M:%S")
                    created_at = c_at + " UTC"
                except Exception:
                    pass

            created_by = getattr(event, 'created_by', None)
            try:
                href = created_by.get('user', {}).get('href')
                user = get_users(href)
            except:
                user = 'unknown'

            resource_name, bouquets_col = extract_resource_name(
                event, is_iplist_event, iplist_href_to_bouquets)

            if is_iplist_event:
                html_parts.append(
                    f"<tr><td>{html.escape(resource_name)}</td><td>{html.escape(created_at)}</td><td>{html.escape(user)}</td><td>{html.escape(bouquets_col)}</td></tr>"
                )
            else:
                html_parts.append(
                    f"<tr><td>{html.escape(resource_name)}</td><td>{html.escape(created_at)}</td><td>{html.escape(user)}</td></tr>"
                )

        html_parts.append("</tbody></table>")
    html_parts.append("<p>Regards,<br>GTS/SEC/STS- Illumio</p>")
    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def send_email(subject, bouquet_event, iplist_ref_to_bouquets, logger):

    html_body = format_events_for_email_html(
        bouquet_event, logger, iplist_ref_to_bouquets)
    """
    Send an email using SMTP.
    """
    msg = MIMEText(html_body, 'html')
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = ', '.join(EMAIL_TO)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        logger.info(f"HTML email sent to {EMAIL_TO} with subject '{subject}'")
    except Exception as e:
        logger.error(f"Failed to send HTML email: {e}")
        raise
