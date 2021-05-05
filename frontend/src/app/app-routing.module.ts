import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import {WordsListComponent} from './components/words-list/words-list.component'

const routes: Routes = [
  { path: '', redirectTo: 'wordlist', pathMatch: 'full'},
  { path: 'word-list', component: WordsListComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
