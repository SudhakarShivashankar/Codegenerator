<?php

namespace App\Http\Controllers\API\v1;

use App\Models\User;
use App\Models\Collation;
use App\Helpers\UserHelpers;
use Illuminate\Http\Request;
use App\Models\UserCollation;
use App\Helpers\CollationHelpers;
use App\Models\UserCollationForm;
use Illuminate\Support\Facades\DB;
use App\Models\UserCollationRating;
use App\Http\Controllers\Controller;

class UserCollationController extends Controller
{
    public function index(Request $request)
    {
        $builder = Collation::listing()
            ->with([
                'userCollations' => function ($q) use ($request) {
                    $q->where('user_id', $request->user_id);
                    $q->where('is_visible', true);
                }
            ])
            ->when($request->country_id, fn ($q) => $q->whereHas(
                'collationCountries',
                fn ($q) => $q->where('country_id',  $request->country_id)
            ));

        return datatables()
            ->of($builder)
            ->escapeColumns([])
            ->toJson();
    }


    public function toggleSelection(User $user, Request $request)
    {
        $this->authorize('update', $user);

        $this->validate($request, [
            'collation_id' => 'required|valid_id',
            'selected'  => 'required|boolean',
        ]);

        $existingUserCollation = UserCollation::where('user_id', $user->id)
            ->where('collation_id', $request->collation_id)
            ->first();

        $userCollation = $existingUserCollation ?: new UserCollation();

        $userCollation->user_id =  $user->id;
        $userCollation->collation_id = $request->collation_id;
        $userCollation->is_visible = $request->selected;
        // Clear requesting approval if collation is no longer selected on profile
        if ($userCollation->is_requesting_approval && !$request->selected) {
            $userCollation->is_requesting_approval = false;
        }

        $userCollation->save();

        $user->num_collations = $user->userCollations()
            ->where('is_visible', true)
            ->count();

        $user->save();
    }

    public function requestApproval(Collation $collation, User $user)
    {
        $this->authorize('update', $user);

        $userCollation = $collation->userCollations()
            ->where('user_id', $user->id)
            ->firstOrFail();

        $userCollation->is_requesting_approval = true;
        $userCollation->save();

        $collationRating = $collation
            ->ratings()
            ->where('user_id', $userCollation->user_id)
            ->first();

        if (!$collationRating) {
            $collationRating = new UserCollationRating();
            $collationRating->user_id = $userCollation->user_id;
            $collationRating->collation_id = $userCollation->collation_id;
            $collationRating->average_level = UserHelpers::calculateCollationAverageLevel($collation, $user);
            $collationRating->save();
        }

        $collationTemplateIds = $collation->collationTemplates->pluck('id');

        UserCollationForm::whereIn('collation_template_id', $collationTemplateIds)
            ->where('status_id', UserCollationForm::STATUS_SUBMITTED)
            ->where('user_id', $user->id)
            ->each(function ($form) {
                $form->status_id = UserCollationForm::STATUS_PENDING;
                $form->save();
                CollationHelpers::sendNotificationToNextReviewer($form);
            });
    }
}
