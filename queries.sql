CREATE OR REPLACE VIEW v_active_org_roles AS 
SELECT orgr.org_role_id, r.role_id, r.role, o.org_id, o.name, ors.status, ors.changed_on
FROM roles r INNER JOIN org_roles orgr ON r.role_id = orgr.role_id INNER JOIN org_role_statuses ors ON orgr.org_role_id = ors.org_role_id INNER JOIN organizations o ON o.org_id = orgr.org_id
WHERE ors.status = 1
ORDER BY orgr.org_role_id;

CREATE OR REPLACE VIEW v_approval_procedure_stages AS
SELECT s.approval_procedure_id, s.stage_id, s.stage_order, s.stage_activity, s.branch_level, s.role_id, ors.org_role_id, ors.role, s.pos_x, s.pos_y, s.icon
FROM v_active_org_roles ors INNER JOIN stages s ON ors.role_id = s.role_id
ORDER BY s.stage_order;

