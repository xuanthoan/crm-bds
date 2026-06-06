import { Badge } from '../../../components/Badge';
export function DepartmentBadge({name}:{name?:string|null}) { return <Badge tone="blue">{name ?? 'Chưa phân bổ'}</Badge>; }
