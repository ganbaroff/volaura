-- EventShift: WUF13 Guest Services (GSE) seed blueprint
-- Source: CEO NotebookLM (ganbarov.y@gmail.com) "World Urban Forum 13 Guest Services Scope of Work"
-- Extracted 2026-04-17 Baku. CEO directive: наши данные в ивентшифт, не оверол.
--
-- Shape: one WUF13 event → one GSE department → 5 areas (Registration + Area A/B/C/D + Boulevard).
-- Full operational blueprint (roles, SOPs, policies, FAQ, metrics, training, callsigns)
-- lives in department.metadata JSONB so the router can surface it as-is to clients.
--
-- Idempotent: guarded by NOT EXISTS on the seed org UUID so re-running does not duplicate.
-- Seed org UUID is a deterministic fixed value scoped to the WUF13 demo tenant.

DO $$
DECLARE
    v_seed_org_id UUID := '00000000-0000-0000-0000-00000000117f'; -- reserved WUF13 demo org
    v_event_id UUID;
    v_dept_id UUID;
BEGIN
    -- Only seed if the demo org row exists (CEO/admin creates it manually once).
    IF NOT EXISTS (SELECT 1 FROM public.organizations WHERE id = v_seed_org_id) THEN
        RAISE NOTICE 'Skipping WUF13 GSE seed: demo org % not present', v_seed_org_id;
        RETURN;
    END IF;

    -- Event: World Urban Forum 13, Baku Olympic Stadium.
    INSERT INTO public.eventshift_events (
        id, org_id, name, slug, start_at, end_at, venue, status, timezone, metadata
    )
    VALUES (
        gen_random_uuid(), v_seed_org_id, 'World Urban Forum 13 — Baku 2026',
        'wuf13-baku-2026',
        '2026-06-17 07:00+04', '2026-06-22 19:00+04',
        'Baku Olympic Stadium',
        'planning', 'Asia/Baku',
        jsonb_build_object(
            'source', 'NotebookLM WUF13 Guest Services Scope of Work',
            'extracted_at', '2026-04-17T16:12:00+04:00',
            'ops_start', '08:00',
            'shifts', jsonb_build_array(
                jsonb_build_object('name', 'Shift 1', 'start', '07:00', 'end', '13:30'),
                jsonb_build_object('name', 'Shift 2', 'start', '12:30', 'end', '19:00'),
                jsonb_build_object('name', 'Handover', 'start', '13:00', 'end', '13:15', 'type', 'joint_duty')
            )
        )
    )
    ON CONFLICT (org_id, slug) DO UPDATE SET metadata = EXCLUDED.metadata
    RETURNING id INTO v_event_id;

    -- Department: Guest Services (GSE)
    INSERT INTO public.eventshift_departments (
        id, org_id, event_id, name, color_hex, sort_order, metadata
    )
    VALUES (
        gen_random_uuid(), v_seed_org_id, v_event_id, 'Guest Services (GSE)',
        '#7C5CFC', 1,
        jsonb_build_object(
            'mission', 'Safe, organized, welcoming frontline service at Baku Olympic Stadium — main interface between venue and guests.',
            'kpis', jsonb_build_array(
                'PSA throughput (people/hour)',
                'Entrance wait time',
                'First-level resolution %',
                'Lost & Found reunited %',
                'Volunteer attendance',
                'Radio response time'
            ),
            'roles', jsonb_build_array(
                jsonb_build_object(
                    'tier', 1, 'title', 'Head / Deputy Head of GSE',
                    'scope', 'Strategic + tactical, coordination with OpCo',
                    'callsign_slots', jsonb_build_array(
                        jsonb_build_object('role', 'Head of GSE',       'callsign', 'Guest-1', 'assignee_user_id', NULL),
                        jsonb_build_object('role', 'Deputy Head',       'callsign', 'Guest-2', 'assignee_user_id', NULL),
                        jsonb_build_object('role', 'Head of Operations','callsign', 'Guest-3', 'assignee_user_id', NULL)
                    )
                ),
                jsonb_build_object(
                    'tier', 2, 'title', 'Zone Manager',
                    'scope', 'Tactical control of zone (Registration, Area A/B/C/D, Boulevard); manages coordinators; mid-level escalations',
                    'callsign_slots', jsonb_build_array(
                        jsonb_build_object('role', 'Registration Manager','callsign', 'Registration-1', 'assignee_user_id', NULL),
                        jsonb_build_object('role', 'Area A Manager',      'callsign', 'A-1',            'assignee_user_id', NULL),
                        jsonb_build_object('role', 'Area B Manager',      'callsign', 'B-1',            'assignee_user_id', NULL),
                        jsonb_build_object('role', 'Area C Manager',      'callsign', 'C-1',            'assignee_user_id', NULL),
                        jsonb_build_object('role', 'Area D Manager',      'callsign', 'D-1',            'assignee_user_id', NULL),
                        jsonb_build_object('role', 'Boulevard Manager',   'callsign', 'BLV-1',          'assignee_user_id', NULL)
                    )
                ),
                jsonb_build_object(
                    'tier', 3, 'title', 'Coordinator',
                    'scope', 'Operational post control; specialist + volunteer briefings; primary incident handling'
                ),
                jsonb_build_object(
                    'tier', 4, 'title', 'Specialist',
                    'scope', 'Queue monitoring, pacemaking, log-keeping, inventory'
                ),
                jsonb_build_object(
                    'tier', 5, 'title', 'Volunteer',
                    'scope', 'Guest greeting, navigation, info, queue (snake) management'
                )
            ),
            'requirements', jsonb_build_array(
                'Professional conduct',
                'Neutrality (no political/religious opinions)',
                'English (primary) + Azerbaijani (local)'
            ),
            'competencies', jsonb_build_array(
                jsonb_build_object('name', 'Professionalism', 'detail', 'WUF13 ethics'),
                jsonb_build_object('name', 'Neutrality', 'detail', 'No political/religious opinions'),
                jsonb_build_object('name', 'Communication', 'detail', 'Fleet Map + radio protocols'),
                jsonb_build_object('name', 'Stress tolerance', 'detail', 'Up to 625 people/hour per frame at PSA'),
                jsonb_build_object('name', 'Proactivity', 'detail', 'Spot congestion, inform guests')
            ),
            'sops', jsonb_build_array(
                jsonb_build_object(
                    'code', 'CP-GSE-Flow',
                    'name', 'Crowd Flow',
                    'trigger', 'Last Mile crowd',
                    'steps', jsonb_build_array(
                        'Activate Pacemaker',
                        'Create buffer zones',
                        'Regulate speed toward PSA'
                    )
                ),
                jsonb_build_object(
                    'code', 'CP-GSE-Queue',
                    'name', 'Queue Management',
                    'trigger', 'Snake 80% full',
                    'steps', jsonb_build_array(
                        'Sort Bags / No Bags',
                        'Redistribute to free PSA lines'
                    )
                ),
                jsonb_build_object(
                    'code', 'CP-GSE-Escalation',
                    'name', 'Escalation',
                    'trigger', 'On-site incident',
                    'steps', jsonb_build_array(
                        'Notify Team Leader',
                        'First-level resolution attempt',
                        'Escalate to Zone Manager',
                        'Log in Incident Log'
                    )
                ),
                jsonb_build_object(
                    'code', 'CP-GSE-Handover',
                    'name', 'Shift Handover',
                    'trigger', '13:00',
                    'steps', jsonb_build_array(
                        'Joint duty 15 min',
                        'Handover notes'
                    )
                ),
                jsonb_build_object(
                    'code', 'CP-GSE-05',
                    'name', 'Stop & Hold',
                    'trigger', 'RB-01 risk: mass egress from B01+B02 dialogue halls (1000m²) → Inner Ring Road 4-5m wide',
                    'steps', jsonb_build_array(
                        'Stop & Hold at room exits',
                        'Regulate corridor inflow'
                    )
                ),
                jsonb_build_object(
                    'code', 'CP-GSE-06',
                    'name', 'Suspicious item',
                    'trigger', 'Unattended object detected',
                    'steps', jsonb_build_array(
                        'Keep 5m distance',
                        'Do not touch',
                        'Notify security + Zone Manager'
                    )
                ),
                jsonb_build_object(
                    'code', 'CP-GSE-07',
                    'name', 'Aggressive delegate',
                    'trigger', 'Guest threatens or escalates verbally',
                    'steps', jsonb_build_array(
                        'De-escalate calmly',
                        'Maintain neutrality',
                        'Call Zone Manager'
                    )
                ),
                jsonb_build_object(
                    'code', 'CP-GSE-07-Flow',
                    'name', 'Registration system failure',
                    'trigger', 'Accreditation system down',
                    'steps', jsonb_build_array(
                        'Switch to manual log',
                        'Pacemaker at entrance',
                        'Notify Registration Manager'
                    )
                ),
                jsonb_build_object(
                    'code', 'A-B-Dot-Plan',
                    'name', 'Staffing shortage plan',
                    'trigger', 'Headcount < required',
                    'steps', jsonb_build_array(
                        'Redistribute from low-load zones',
                        'Activate backup roster',
                        'Notify Head of GSE'
                    )
                )
            ),
            'policies', jsonb_build_object(
                'do', jsonb_build_array(
                    'Follow communication hierarchy',
                    'Log all incidents',
                    'Wear accreditation + uniform',
                    'Maintain neutrality'
                ),
                'dont', jsonb_build_array(
                    'Argue with guests',
                    'Leave post before relief arrives',
                    'Disclose confidential data',
                    'Touch suspicious items (keep 5m distance)'
                )
            ),
            'metrics', jsonb_build_array(
                jsonb_build_object('name', 'Flow Rate', 'unit', 'people/minute', 'corridor_limit', '328-451'),
                jsonb_build_object('name', 'Wait Time', 'detail', 'Avg queue wait at Registration'),
                jsonb_build_object('name', 'Incident Resolution', 'detail', '% complaints closed by end of shift'),
                jsonb_build_object('name', 'Response Time', 'detail', 'Specialist arrival after call')
            ),
            'training', jsonb_build_object(
                'briefing_topics', jsonb_build_array(
                    'Day program overview',
                    'Expected peak loads',
                    'Safety reminders'
                ),
                'checklists', jsonb_build_array(
                    'Radio / headset check',
                    'Zone map availability',
                    'Info Point readiness'
                ),
                'incident_scenarios', jsonb_build_array(
                    'CP-GSE-06 suspicious item',
                    'CP-GSE-07 aggressive delegate',
                    'CP-GSE-07-Flow registration system failure',
                    'A-B Dot Plan staffing shortage'
                )
            ),
            'faq', jsonb_build_array(
                jsonb_build_object('q', 'Badge', 'a', 'Registration'),
                jsonb_build_object('q', 'Schedule', 'a', 'Info Points'),
                jsonb_build_object('q', 'Storage', 'a', 'Registration / Service Hub'),
                jsonb_build_object('q', 'SIM', 'a', 'Service Hub Area B'),
                jsonb_build_object('q', 'Medical', 'a', 'Area A / Area B'),
                jsonb_build_object('q', 'VIP Lounge', 'a', 'Area D'),
                jsonb_build_object('q', 'IMEI', 'a', 'Service Hub / Post'),
                jsonb_build_object('q', 'Bilateral Hub', 'a', 'Area A'),
                jsonb_build_object('q', 'Media Hub', 'a', 'Area B'),
                jsonb_build_object('q', 'Mother & Child', 'a', 'Area B U04'),
                jsonb_build_object('q', 'Prayer rooms', 'a', 'Area B U05/U06'),
                jsonb_build_object('q', 'Vet room', 'a', 'Area B CC08'),
                jsonb_build_object('q', 'Transport', 'a', 'Transport Desk Area B'),
                jsonb_build_object('q', 'ATM', 'a', 'Service Hub'),
                jsonb_build_object('q', 'Lost & Found', 'a', 'Service Hub'),
                jsonb_build_object('q', 'Welcome Bag', 'a', 'Registration'),
                jsonb_build_object('q', 'Speaker Lounge', 'a', 'Area B U07'),
                jsonb_build_object('q', 'Food court', 'a', 'Area B'),
                jsonb_build_object('q', 'Playground', 'a', 'Area B')
            )
        )
    )
    ON CONFLICT (event_id, name) DO UPDATE SET metadata = EXCLUDED.metadata
    RETURNING id INTO v_dept_id;

    -- Areas: 5 zones under GSE.
    INSERT INTO public.eventshift_areas (org_id, department_id, name, description, sort_order, metadata)
    VALUES
        (v_seed_org_id, v_dept_id, 'Registration', 'Accreditation + badges + welcome bag',       1, '{"zone_code": "REG"}'::jsonb),
        (v_seed_org_id, v_dept_id, 'Area A',       'Bilateral Hub, Medical (A)',                  2, '{"zone_code": "A"}'::jsonb),
        (v_seed_org_id, v_dept_id, 'Area B',       'Media Hub, Service Hub, Mother&Child, Prayer, Vet, Speaker Lounge, Food, Playground', 3, jsonb_build_object('zone_code','B','staffing', jsonb_build_object('manager',1,'coordinators',2,'specialists',4,'volunteers',44))),
        (v_seed_org_id, v_dept_id, 'Area C',       'General programme',                           4, '{"zone_code": "C"}'::jsonb),
        (v_seed_org_id, v_dept_id, 'Area D',       'VIP Lounge',                                  5, '{"zone_code": "D"}'::jsonb),
        (v_seed_org_id, v_dept_id, 'Boulevard',    'Outer approach — Last Mile crowd flow',       6, '{"zone_code": "BLV"}'::jsonb)
    ON CONFLICT (department_id, name) DO UPDATE SET metadata = EXCLUDED.metadata;

    RAISE NOTICE 'WUF13 GSE seed applied: event=%, dept=%', v_event_id, v_dept_id;
END $$;

-- ============================================================
-- Also update the eventshift module settings_schema so the catalogue
-- advertises what a department config looks like for other tenants.
-- ============================================================
UPDATE public.modules
SET settings_schema = jsonb_build_object(
    'department', jsonb_build_object(
        'required', jsonb_build_array('mission', 'kpis', 'roles'),
        'optional', jsonb_build_array('requirements', 'competencies', 'sops', 'policies', 'metrics', 'training', 'faq')
    ),
    'shift', jsonb_build_object(
        'required', jsonb_build_array('name', 'start', 'end'),
        'optional', jsonb_build_array('type')
    ),
    'sop', jsonb_build_object(
        'required', jsonb_build_array('code', 'name', 'trigger', 'steps')
    )
)
WHERE slug = 'eventshift';
