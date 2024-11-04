<?php

namespace App\Helpers;

use App\Mail\CollationFormReviewerMail;
use App\Models\Collation;
use App\Models\CollationItem;
use App\Models\User;
use App\Models\UserCollation;
use App\Models\UserCollationForm;
use App\Models\UserCollationFormReviewer;
use App\Models\UserCollationRating;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Mail;

abstract class CollationHelpers
{
    /**
     * Checks to see if any collations can be added to the users profile if they have met the collation % threshold
     */
    public static function addMissingCollations(User $user): void
    {
        $numSelectedItemsBuilder = self::getSelectedCollationItemBuilder($user);

        $totalItemsBuilder = CollationItem::selectRaw('COUNT(*) as count, collation_id')
            ->groupBy('collation_id');

        $userCollations = Collation::whereHas('collationCountries', fn($q) => $q->where('country_id', $user->office->country_id))
            ->whereDoesntHave('userCollations', fn($q) => $q->where('user_id', $user->id))
            ->select([
                'collations.id',
                'total_items.count as total_items',
                DB::raw('COALESCE(num_selected.count, 0) as num_selected_items')
            ])
            ->joinSub($totalItemsBuilder, 'total_items', 'total_items.collation_id', 'collations.id')
            ->leftJoinSub($numSelectedItemsBuilder, 'num_selected', 'num_selected.collation_id', 'collations.id')
            ->whereRaw('((num_selected.count / total_items.count::float) * 100)  >= collations.notification_threshold')
            ->get()
            ->map(fn($collation) => [
                'collation_id' => $collation->id,
                'user_id' => $user->id,
                'is_visible' => true
            ]);

        UserCollation::insert($userCollations->toArray());

        $user->num_collations = $user->userCollations()
            ->where('is_visible', true)
            ->count();

        $user->save();
    }

    private static function getSelectedCollationItemBuilder(User $user): Builder
    {
        return CollationItem::selectRaw('COUNT(*) as count, collation_id')
            ->whereHasMorph(
                'collationable',
                '*',
                fn($q) => $q->whereHas('userCollationItems', fn($q) => $q->where('user_id', $user->id))
            )
            ->groupBy('collation_id');
    }

    /**
     * Fetch a list of collations applicable to the given user
     */
    public static function getCollations(User $user): Collection
    {
        // Include the approved overall user rating for each collation (if available)
        $eagerloadLatestRating = function ($q) use ($user) {
            $q->where('user_collation_ratings.user_id', $user->id);
            $q->listing();
        };

        return $user->collations()
            ->where('user_collations.is_visible', true)
            ->with([
                'latestUserCollationRating' => $eagerloadLatestRating,
                'approvers:users.id,name,email',
                'collationTemplates' => function ($q) use ($user) {
                    $q->leftJoin('user_collation_forms as ucf', function ($q) use ($user) {
                        $q->on('ucf.collation_template_id', '=', 'collation_templates.id');
                        $q->where('ucf.user_id', $user->id);
                    });
                    $q->leftJoin('lookups as st', 'st.id', '=', 'ucf.status_id');
                    $q->orderBy('id', 'asc');
                    $q->selectRaw(
                        "collation_templates.*,
                        ucf.updated_at as user_collation_form_updated_at,
                        ucf.status_id,
                        st.value as user_collation_form_status,
                        st.meta1 as status_cls,
                        ucf.id as user_collation_form_id"
                    );
                },
            ])
            ->leftJoin('user_collations as ucc', function ($q) use ($user) {
                $q->on('ucc.collation_id', '=', 'collations.id');
                $q->where('ucc.user_id', $user->id);
            })
            ->select([
                'collations.*',
                'ucc.is_requesting_approval as user_collation_request_approval'
            ])
            ->withAvg(['capabilities as average_level' => function ($q) use ($user) {
                $q->join('user_capabilities as uc', function ($q) use ($user) {
                    $q->on('uc.capability_id', '=', 'capabilities.id');
                    $q->where('uc.user_id', $user->id);
                    $q->whereNull('uc.deleted_at');
                });
            }], 'uc.level')
            ->orderBy('collations.name')
            ->get();
    }

    /**
     * Fetch some aggregations for the given collation and user
     */
    public static function getCollationSummary(User $user): Collection
    {
        $numSelectedItemsBuilder = self::getSelectedCollationItemBuilder($user);

        return $user->collations()
            ->where('user_collations.is_visible', true)
            ->leftJoinSub($numSelectedItemsBuilder, 'num_selected', 'num_selected.collation_id', 'collations.id')
            ->with([
                'certificates' => function ($q) use ($user) {
                    $q->leftJoin('user_professional_certificates as upc', function ($q) use ($user) {
                        $q->on('upc.certificate_id', '=', 'professional_certificates.id');
                        $q->where('user_id', $user->id);
                    });
                    $q->select([
                        'professional_certificates.id as certificate_id',
                        'professional_certificates.name',
                        'professional_certificates.country_id',
                        'upc.expiry_date',
                        'upc.id as user_professional_certificate_id'
                    ]);
                },
                'healthSafetyCertificates' => function ($q) use ($user) {
                    $q->leftJoin('user_health_safety_certificates as uhs', function ($q) use ($user) {
                        $q->on('uhs.certificate_id', '=', 'health_safety_certificates.id');
                        $q->where('user_id', $user->id);
                    });
                    $q->select([
                        'health_safety_certificates.id as certificate_id',
                        'health_safety_certificates.name',
                        'uhs.expiry_date',
                        'uhs.id as user_health_safety_certificate_id'
                    ]);
                },
                'medicals' => function ($q) use ($user) {
                    $q->leftJoin('user_medicals as um', function ($q) use ($user) {
                        $q->on('um.medical_certificate_id', '=', 'medical_certificates.id');
                        $q->where('user_id', $user->id);
                    });
                    $q->select([
                        'medical_certificates.id as medical_certificate_id',
                        'medical_certificates.name',
                        'medical_certificates.next_test_year',
                        'um.next_due_date',
                        'um.id as user_medical_id'
                    ]);
                },
                'securityClearanceTypes' => function ($q) use ($user) {
                    $q->leftJoin('user_security_clearances as usc', function ($q) use ($user) {
                        $q->on('usc.type_id', '=', 'security_clearance_types.id');
                        $q->where('user_id', $user->id);
                    });
                    $q->select([
                        'security_clearance_types.id as type_id',
                        'security_clearance_types.name',
                        'security_clearance_types.country_id',
                        'usc.expiry_date',
                        'usc.id as user_security_clearance_id'
                    ]);
                },
                'capabilities' => function ($q) use ($user) {
                    $q->leftJoin('user_capabilities as uca', function ($q) use ($user) {
                        $q->on('uca.capability_id', '=', 'capabilities.id');
                        $q->where('uca.user_id', $user->id);
                        $q->whereNull('uca.deleted_at');
                    })
                        ->leftJoin('lookups as st', 'st.id', '=', 'uca.status_id')
                        ->leftJoin('users as u', 'u.id', '=', 'uca.approved_by');

                    $q->select([
                        'capabilities.id as capability_id',
                        'capabilities.name',
                        'capabilities.requires_rating',
                        'uca.id as user_capability_id',
                        'uca.status_id',
                        'uca.level',
                        'uca.approved_at',
                        'st.value as status',
                        'st.meta1 as status_cls',
                        'u.name as approved_by'
                    ]);
                },
                'training' => function ($q) use ($user) {
                    $q->leftJoin('user_training as ut', function ($q) use ($user) {
                        $q->on('ut.training_id', '=', 'training.id');
                        $q->where('user_id', $user->id);
                    });
                    $q->select([
                        'training.id',
                        'training.name',
                        'training.training_url',
                        'training.country_id',
                        'ut.completed_at',
                        'ut.id as user_training_id'
                    ]);
                    $q->orderBy('training.name');
                },
            ])

            ->withCount('collationItems as total_collation_items')

            ->withCount('collationTemplates as total_questionnaire_count')

            ->withCount(['collationTemplates as total_reviewed_questionnaire_count' => function ($q) use ($user) {
                $q->join('user_collation_forms as uff', function ($q) use ($user) {
                    $q->on('uff.collation_template_id', '=', 'collation_templates.id');
                    $q->where('uff.status_id', UserCollationForm::STATUS_REVIEWED);
                    $q->where('uff.user_id', $user->id);
                });
            }])

            ->withCount(['collationTemplates as total_submitted_questionnaire_count' => function ($q) use ($user) {
                $q->join('user_collation_forms as uff', function ($q) use ($user) {
                    $q->on('uff.collation_template_id', '=', 'collation_templates.id');
                    $q->where('uff.status_id', UserCollationForm::STATUS_SUBMITTED);
                    $q->where('uff.user_id', $user->id);
                });
            }])

            ->withAvg(['capabilities as average_level' => function ($q) use ($user) {
                $q->join('user_capabilities as uc', function ($q) use ($user) {
                    $q->on('uc.capability_id', '=', 'capabilities.id');
                    $q->where('uc.user_id', $user->id);
                    $q->whereNull('uc.deleted_at');
                });
            }], 'uc.level')

            ->withSum(['capabilities as total_level' => function ($q) use ($user) {
                $q->join('user_capabilities as uc', function ($q) use ($user) {
                    $q->on('uc.capability_id', '=', 'capabilities.id');
                    $q->where('uc.user_id', $user->id);
                    $q->whereNull('uc.deleted_at');
                });
            }], 'uc.level')

            ->addSelect([DB::raw('COALESCE(num_selected.count, 0) as total_selected_collation_items')])

            ->get();
    }

    public static function sendNotificationToNextReviewer(UserCollationForm $userCollationForm, $sequence = 1): UserCollationFormReviewer|bool
    {
        $userCollationFormReviewer = $userCollationForm->reviewers()
            ->where('sequence', $sequence)
            ->whereNull('is_approved')
            ->first();

        if (!$userCollationFormReviewer) return false;
        if ($userCollationFormReviewer->is_reviewer_notified) return false;

        Mail::to($userCollationFormReviewer->reviewer)
            ->queue(new CollationFormReviewerMail($userCollationForm, $userCollationFormReviewer));

        $userCollationFormReviewer->is_reviewer_notified = true;
        $userCollationFormReviewer->save();

        return $userCollationFormReviewer;
    }

    public static function getCollationApprovalBuilder(User $user): Builder
    {
        return UserCollation::excludingDeletedUsers()
            ->where('is_requesting_approval', true)
            ->whereIn('collation_id', $user->collationApprovers->pluck('collation_id'))
            ->listing()
            ->with('user:id,name,email,job_title')
            ->orderBy('user_collations.updated_at', 'desc');
    }

    public static function getUserCollationFormsToReviewBuilder(User $reviewer): Builder
    {
        $previousReviewBuilder = UserCollationFormReviewer::selectRaw(1)
            ->from('user_collation_form_reviewers as preview_reviewers')
            ->whereColumn('user_collation_form_reviewers.user_collation_form_id', 'preview_reviewers.user_collation_form_id')
            ->whereColumn('preview_reviewers.sequence', DB::raw('user_collation_form_reviewers.sequence - 1'))
            ->where('is_approved', true);

        return UserCollationForm::query()
            ->with('user:id,name,email,job_title')
            ->whereHas('reviewers', function ($q) use ($reviewer, $previousReviewBuilder) {
                $q->where('reviewer_id', $reviewer->id);
                $q->whereNull('is_approved');
                $q->where(function ($q) use ($previousReviewBuilder) {
                    $q->where('sequence', 1);
                    $q->orWhereExists($previousReviewBuilder);
                });
            });
    }

    public static function getApprovedCollationRatings($user): Collection
    {
        return UserCollationRating::listing()
            ->where('user_collation_ratings.user_id', $user->id)
            ->whereNotNull('approved_at')
            ->get();
    }
}
