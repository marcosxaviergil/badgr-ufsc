import {Component, OnInit} from '@angular/core';
import {FormBuilder, Validators} from '@angular/forms';
import {ActivatedRoute, Router} from '@angular/router';
import {MessageService} from '../../../common/services/message.service';
import {SessionService} from '../../../common/services/session.service';
import {Title} from '@angular/platform-browser';

import {CommonDialogsService} from '../../../common/services/common-dialogs.service';
import {BaseAuthenticatedRoutableComponent} from '../../../common/pages/base-authenticated-routable.component';
import {UserProfileManager} from '../../../common/services/user-profile-manager.service';
import {UserProfile} from '../../../common/model/user-profile.model';
import {AppConfigService} from '../../../common/app-config.service';
import {typedFormGroup} from '../../../common/util/typed-forms';
import { LinkEntry } from "../../../common/components/bg-breadcrumbs/bg-breadcrumbs.component";

@Component({
	templateUrl: './profile-edit.component.html',
})
export class ProfileEditComponent extends BaseAuthenticatedRoutableComponent implements OnInit {
	profile: UserProfile;
	isUfscUser: boolean = false;  // ✅ NOVO: Flag para usuário UFSC
	profileEditForm = typedFormGroup()
		.addControl("firstName", "", Validators.required)
		.addControl("lastName", "", Validators.required)
	;

	profileLoaded: Promise<unknown>;
	crumbs: LinkEntry[] = [
		{title: 'Profile', routerLink: ['/profile']},
		{title: 'Edit Profile', routerLink: ['/profile/edit']},
	];

	constructor(
		router: Router,
		route: ActivatedRoute,
		sessionService: SessionService,
		protected formBuilder: FormBuilder,
		protected title: Title,
		protected messageService: MessageService,
		protected profileManager: UserProfileManager,
		protected configService: AppConfigService,
		protected dialogService: CommonDialogsService
) {
		super(router, route, sessionService);
		title.setTitle(`Profile - Edit - ${this.configService.theme['serviceName'] || "Badgr"}`);

		this.profileLoaded = profileManager.userProfilePromise.then(
			profile => {
				this.profile = profile;
				// ✅ CORREÇÃO: Primeiro carregar o form, depois verificar UFSC
				this.startEditing();
				this.checkIfUfscUser();
			},
			error => this.messageService.reportAndThrowError(
				"Failed to load userProfile", error
			)
		);
	}

	// ✅ CORREÇÃO: Aguardar carregamento completo dos socialAccounts
	checkIfUfscUser() {
		if (this.profile && this.profile.socialAccounts) {
			this.profile.socialAccounts.loadedPromise.then(() => {
				this.isUfscUser = this.profile.socialAccounts.entities.some(
					account => account.providerSlug === 'ufsc'
				);
				
				// ✅ CORREÇÃO: Aplicar desabilitação SOMENTE após verificação
				if (this.isUfscUser) {
					// Usar setTimeout para garantir que o DOM foi atualizado
					setTimeout(() => {
						this.profileEditForm.rawControlMap.firstName.disable();
						this.profileEditForm.rawControlMap.lastName.disable();
					}, 0);
				}
			}).catch(() => {
				// Em caso de erro, assumir que não é UFSC
				this.isUfscUser = false;
			});
		}
	}

	startEditing() {
		// ✅ CORREÇÃO: Sempre preencher os campos primeiro
		this.profileEditForm.setValue({
			firstName: this.profile.firstName || '',
			lastName: this.profile.lastName || ''
		}, { emitEvent: false });
	}

	submitEdit() {
		// ✅ BLOQUEIO: Impedir submit se for usuário UFSC
		if (this.isUfscUser) {
			this.messageService.reportHandledError(
				'Profile name changes are managed through your institutional UFSC account.'
			);
			return;
		}

		if (! this.profileEditForm.markTreeDirtyAndValidate()) {
			return;
		}

		const formValue = this.profileEditForm.value;

		this.profile.firstName = formValue.firstName;
		this.profile.lastName = formValue.lastName;

		this.profile.save().then(
			() => {
				this.messageService.reportMinorSuccess(`Saved profile changes`);
				this.router.navigate(['/profile/profile']);
			},
			error => {
				this.messageService.reportHandledError(`Failed save profile changes`, error);
			}
		);
	}
}