export const Platform = {
    YouTube: 'YouTube',
    OTT: 'OTT',
    Airline: 'Airline',
    SocialMedia: 'Social Media',
} as const;
export type Platform = typeof Platform[keyof typeof Platform];

export const Rating = {
    Kids: 'Kids (G)',
    Teens: 'Teens (PG-13)',
    Adult: 'Adult (R)',
} as const;
export type Rating = typeof Rating[keyof typeof Rating];

export const Region = {
    Global: 'Global',
    MiddleEast: 'Middle East',
    EastAsia: 'East Asia',
    Europe: 'Europe',
} as const;
export type Region = typeof Region[keyof typeof Region];

export const RemediationAction = {
    OBJECT_REPLACE: 'OBJECT_REPLACE',
    PIXELATE: 'PIXELATE',
    BLUR: 'BLUR',
    WORD_DUB: 'WORD_DUB',
    BEEP: 'BEEP',
    MUTE: 'MUTE',
    BLOCK_SEGMENT: 'BLOCK_SEGMENT',
    ALLOWED: 'ALLOWED',
} as const;
export type RemediationAction = typeof RemediationAction[keyof typeof RemediationAction];

export interface PolicyRules {
    alcohol: RemediationAction;
    skin: RemediationAction;
    religion: RemediationAction;
    tobacco: RemediationAction;
    drugs: RemediationAction;
    weapons: RemediationAction;
    profanity_all: RemediationAction;
    profanity_strong: RemediationAction;
    logos: RemediationAction;
}

export interface EnforcementObject {
    profile_name: string;
    rules: PolicyRules;
}

const actionStrictness: Record<RemediationAction, number> = {
    [RemediationAction.BLOCK_SEGMENT]: 10,
    [RemediationAction.PIXELATE]: 9,
    [RemediationAction.BLUR]: 8,
    [RemediationAction.OBJECT_REPLACE]: 7,
    [RemediationAction.WORD_DUB]: 6,
    [RemediationAction.MUTE]: 5,
    [RemediationAction.BEEP]: 4,
    [RemediationAction.ALLOWED]: 0,
};

const getStricterAction = (a: RemediationAction, b: RemediationAction): RemediationAction => {
    return (actionStrictness[a] || 0) >= (actionStrictness[b] || 0) ? a : b;
};

export const resolvePolicy = (
    platform: Platform | string,
    rating: Rating | string,
    region: Region | string
): EnforcementObject => {
    // STEP 1: Default 'Standard' rule set
    let rules: PolicyRules = {
        alcohol: RemediationAction.ALLOWED,
        skin: RemediationAction.ALLOWED,
        religion: RemediationAction.ALLOWED,
        tobacco: RemediationAction.ALLOWED,
        drugs: RemediationAction.ALLOWED,
        weapons: RemediationAction.ALLOWED,
        profanity_all: RemediationAction.ALLOWED,
        profanity_strong: RemediationAction.ALLOWED,
        logos: RemediationAction.ALLOWED,
    };

    const updateRule = (category: keyof PolicyRules, action: RemediationAction) => {
        rules[category] = getStricterAction(rules[category], action);
    };

    // STEP 2: Regional Overrides
    if (region === Region.MiddleEast) {
        updateRule('alcohol', RemediationAction.BLOCK_SEGMENT);
        updateRule('skin', RemediationAction.PIXELATE);
        updateRule('religion', RemediationAction.BLUR);
    } else if (region === Region.EastAsia) {
        updateRule('tobacco', RemediationAction.PIXELATE);
        updateRule('drugs', RemediationAction.BLOCK_SEGMENT);
    }

    // STEP 3: Rating Overrides
    if (rating === Rating.Kids) {
        updateRule('alcohol', RemediationAction.OBJECT_REPLACE);
        updateRule('weapons', RemediationAction.OBJECT_REPLACE);
        updateRule('profanity_all', RemediationAction.BEEP);
        updateRule('tobacco', RemediationAction.PIXELATE);
    } else if (rating === Rating.Teens) {
        updateRule('profanity_strong', RemediationAction.WORD_DUB);
        updateRule('weapons', RemediationAction.BLUR);
    }

    // STEP 4: Platform Requirements
    if (platform === Platform.YouTube || platform === Platform.SocialMedia) {
        updateRule('logos', RemediationAction.BLUR);
    } else if (platform === Platform.Airline) {
        updateRule('profanity_strong', RemediationAction.BEEP);
        updateRule('weapons', RemediationAction.PIXELATE);
    }

    const profile_name = `${platform}_${rating}_${region}`.replace(/\s+/g, '_');

    return {
        profile_name,
        rules,
    };
};
