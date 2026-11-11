export function getErrorMessage(error, t) {
  if (!error) return t.genericError;
  if (error.name === "TypeError" || !error.status) return t.networkError;
  if (error.status === 401) return t.genericError;
  if (error.status === 400 || error.status === 422) return t.invalidRequest;
  if (error.status === 403) return t.notAuthorized;
  if (error.status === 404) return t.notFound;
  if (error.status === 409) return t.conflict;
  if (error.status === 429) return t.rateLimited;
  if (error.status === 408) return t.requestTimeout;
  if (error.status === 503) return t.serviceUnavailable;
  return error.message || t.genericError;
}

export function ownerNarrativeStatusLabel(narrative, t) {
  return narrative?.review_status
    ? reviewStatusLabel(narrative.review_status, t)
    : narrativeStatusLabel(narrative?.status, t);
}

export function ownerNarrativeTone(narrative) {
  if (narrative?.review_status === "reviewed") return "success";
  if (narrative?.review_status === "requires_escalation") return "warning";
  return "accent";
}

export function roleLabel(role, t) {
  const labels = {
    community_member: t.communityMember,
    chw: t.chw,
    reviewer: t.reviewer,
    administrator: t.administrator,
  };
  return labels[role] || role || t.communityMember;
}

export function accountStatusLabel(status, t) {
  return {
    active: t.active,
    pending: t.pending,
    suspended: t.suspended,
    deactivated: t.deactivated,
    deleted: t.deleted,
  }[status] || status || t.pending;
}

export function invitationStatusLabel(status, t) {
  return {
    pending: t.pending,
    accepted: t.accepted,
    revoked: t.revoked,
    expired: t.expired,
  }[status] || status || t.pending;
}

export function narrativeStatusLabel(status, t) {
  return {
    submitted: t.submitted,
  }[status] || status || t.submitted;
}

export function reviewStatusLabel(status, t) {
  return {
    pending: t.pendingReview,
    in_review: t.inReview,
    reviewed: t.reviewed,
    requires_escalation: t.requiresEscalation,
  }[status] || status || t.pendingReview;
}

export function questionStatusLabel(status, t) {
  return {
    pending: t.questionPending,
    awaiting_review: t.questionAwaitingReview,
    responded: t.questionResponded,
  }[status] || status || t.questionPending;
}

export function outcomeLabel(outcome, t) {
  return {
    needs_further_review: t.needsFurtherReview,
    evidence_supports_claim: t.evidenceSupportsClaim,
    evidence_does_not_support_claim: t.evidenceDoesNotSupportClaim,
    insufficient_evidence: t.insufficientEvidence,
  }[outcome] || outcome || t.needsFurtherReview;
}

export function formatDate(value, language = "en") {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(language === "rw" ? "rw-RW" : "en-US", {
    dateStyle: "medium",
  }).format(date);
}
