import { Badge } from '../../../components/Badge';
export function TeamBadge({name}:{name?:string|null}) { return <Badge tone="orange">{name ?? 'Chưa có nhóm'}</Badge>; }
