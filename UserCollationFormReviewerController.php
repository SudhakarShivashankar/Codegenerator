<?php

namespace App\Http\Controllers\API\v1;

use App\Helpers\CollationHelpers;
use App\Http\Controllers\Controller;
use App\Http\Requests\API\v1\UserCollationFormReviewerApprovalRequest;
use App\Models\User;
use App\Models\UserCollationForm;
use App\Models\UserCollationFormReviewer;
use Illuminate\Http\Request;

class UserCollationFormReviewerController extends Controller
{
    public function index(User $user)
    {
        return UserCollationFormReviewer::listing()
            ->whereHas('userCollationForm', fn ($q) => $q->where('user_id', $user->id))
            ->orderBy('sequence')
            ->get();
    }

    public function store(UserCollationForm $userCollationForm, Request $request)
    {
        $user = $request->user();
        $this->authorize('rate', $userCollationForm->collationTemplate->collation);

        $this->validate($request, [
            'reviewers_ids' => 'required|array',
            'reviewers_ids.*' => 'valid_id'
        ], ['reviewers_ids.required' => 'Select at least one reviewer']);

        $userCollationForm->reviewers()->delete();

        foreach ($request->reviewers_ids as $index => $reviewerId) {
            $userCollationFormReviewer = new UserCollationFormReviewer();
            $userCollationFormReviewer->reviewer()->associate($reviewerId);
            $userCollationFormReviewer->userCollationForm()->associate($userCollationForm->id);
            $userCollationFormReviewer->sequence = $index + 1;
            $userCollationFormReviewer->setUserRelations($user);
            $userCollationFormReviewer->save();
        }
        CollationHelpers::sendNotificationToNextReviewer($userCollationForm);
    }

    public function show(string $id)
    {
        //
    }

    public function update(UserCollationFormReviewerApprovalRequest $request, UserCollationFormReviewer $userCollationFormReviewer)
    {
        $userCollationForm = $userCollationFormReviewer->userCollationForm;
        $this->authorize('review', $userCollationForm);

        $userCollationFormReviewer->is_approved = $request->is_approved;
        $userCollationFormReviewer->actioned_by = $request->user()->id;
        $userCollationFormReviewer->actioned_at = now();
        $userCollationFormReviewer->comments = $request->comments;
        $userCollationFormReviewer->save();

        if ($userCollationFormReviewer->is_approved === false) {
            $userCollationForm->deny($request->profile_user_id);
        } else {
            $nextReviewer = $userCollationForm->reviewers()
                ->whereNull('is_approved')
                ->orderBy('sequence')
                ->first();

            if (CollationHelpers::sendNotificationToNextReviewer($userCollationForm, $nextReviewer?->sequence) === false) {
                $userCollationForm->status_id = UserCollationForm::STATUS_REVIEWED;
                $userCollationForm->save();
            }
        }
    }

    public function destroy(string $id)
    {
        //
    }
}
