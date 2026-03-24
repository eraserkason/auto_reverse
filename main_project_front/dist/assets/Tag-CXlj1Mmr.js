import{F as so,cG as to,bw as e,c as io,a as u,K as m,Q as I,b as z,d as ho,an as U,h as x,b8 as go,u as bo,e as K,ai as Co,J as vo,r as uo,O as po,C as j,ak as d,bB as fo,cH as D,p as ko,P as mo,H as xo}from"./index-CrjpUL23.js";function Po(c){const{textColor2:g,primaryColorHover:r,primaryColorPressed:p,primaryColor:a,infoColor:i,successColor:n,warningColor:s,errorColor:t,baseColor:f,borderColor:k,opacityDisabled:b,tagColor:S,closeIconColor:P,closeIconColorHover:v,closeIconColorPressed:o,borderRadiusSmall:l,fontSizeMini:C,fontSizeTiny:h,fontSizeSmall:B,fontSizeMedium:H,heightMini:$,heightTiny:R,heightSmall:M,heightMedium:T,closeColorHover:_,closeColorPressed:E,buttonColor2Hover:O,buttonColor2Pressed:w,fontWeightStrong:W}=c;return Object.assign(Object.assign({},to),{closeBorderRadius:l,heightTiny:$,heightSmall:R,heightMedium:M,heightLarge:T,borderRadius:l,opacityDisabled:b,fontSizeTiny:C,fontSizeSmall:h,fontSizeMedium:B,fontSizeLarge:H,fontWeightStrong:W,textColorCheckable:g,textColorHoverCheckable:g,textColorPressedCheckable:g,textColorChecked:f,colorCheckable:"#0000",colorHoverCheckable:O,colorPressedCheckable:w,colorChecked:a,colorCheckedHover:r,colorCheckedPressed:p,border:`1px solid ${k}`,textColor:g,color:S,colorBordered:"rgb(250, 250, 252)",closeIconColor:P,closeIconColorHover:v,closeIconColorPressed:o,closeColorHover:_,closeColorPressed:E,borderPrimary:`1px solid ${e(a,{alpha:.3})}`,textColorPrimary:a,colorPrimary:e(a,{alpha:.12}),colorBorderedPrimary:e(a,{alpha:.1}),closeIconColorPrimary:a,closeIconColorHoverPrimary:a,closeIconColorPressedPrimary:a,closeColorHoverPrimary:e(a,{alpha:.12}),closeColorPressedPrimary:e(a,{alpha:.18}),borderInfo:`1px solid ${e(i,{alpha:.3})}`,textColorInfo:i,colorInfo:e(i,{alpha:.12}),colorBorderedInfo:e(i,{alpha:.1}),closeIconColorInfo:i,closeIconColorHoverInfo:i,closeIconColorPressedInfo:i,closeColorHoverInfo:e(i,{alpha:.12}),closeColorPressedInfo:e(i,{alpha:.18}),borderSuccess:`1px solid ${e(n,{alpha:.3})}`,textColorSuccess:n,colorSuccess:e(n,{alpha:.12}),colorBorderedSuccess:e(n,{alpha:.1}),closeIconColorSuccess:n,closeIconColorHoverSuccess:n,closeIconColorPressedSuccess:n,closeColorHoverSuccess:e(n,{alpha:.12}),closeColorPressedSuccess:e(n,{alpha:.18}),borderWarning:`1px solid ${e(s,{alpha:.35})}`,textColorWarning:s,colorWarning:e(s,{alpha:.15}),colorBorderedWarning:e(s,{alpha:.12}),closeIconColorWarning:s,closeIconColorHoverWarning:s,closeIconColorPressedWarning:s,closeColorHoverWarning:e(s,{alpha:.12}),closeColorPressedWarning:e(s,{alpha:.18}),borderError:`1px solid ${e(t,{alpha:.23})}`,textColorError:t,colorError:e(t,{alpha:.1}),colorBorderedError:e(t,{alpha:.08}),closeIconColorError:t,closeIconColorHoverError:t,closeIconColorPressedError:t,closeColorHoverError:e(t,{alpha:.12}),closeColorPressedError:e(t,{alpha:.18})})}const yo={common:so,self:Po},Io={color:Object,type:{type:String,default:"default"},round:Boolean,size:String,closable:Boolean,disabled:{type:Boolean,default:void 0}},zo=io("tag",`
 --n-close-margin: var(--n-close-margin-top) var(--n-close-margin-right) var(--n-close-margin-bottom) var(--n-close-margin-left);
 white-space: nowrap;
 position: relative;
 box-sizing: border-box;
 cursor: default;
 display: inline-flex;
 align-items: center;
 flex-wrap: nowrap;
 padding: var(--n-padding);
 border-radius: var(--n-border-radius);
 color: var(--n-text-color);
 background-color: var(--n-color);
 transition: 
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 line-height: 1;
 height: var(--n-height);
 font-size: var(--n-font-size);
`,[u("strong",`
 font-weight: var(--n-font-weight-strong);
 `),m("border",`
 pointer-events: none;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border-radius: inherit;
 border: var(--n-border);
 transition: border-color .3s var(--n-bezier);
 `),m("icon",`
 display: flex;
 margin: 0 4px 0 0;
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 font-size: var(--n-avatar-size-override);
 `),m("avatar",`
 display: flex;
 margin: 0 6px 0 0;
 `),m("close",`
 margin: var(--n-close-margin);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),u("round",`
 padding: 0 calc(var(--n-height) / 3);
 border-radius: calc(var(--n-height) / 2);
 `,[m("icon",`
 margin: 0 4px 0 calc((var(--n-height) - 8px) / -2);
 `),m("avatar",`
 margin: 0 6px 0 calc((var(--n-height) - 8px) / -2);
 `),u("closable",`
 padding: 0 calc(var(--n-height) / 4) 0 calc(var(--n-height) / 3);
 `)]),u("icon, avatar",[u("round",`
 padding: 0 calc(var(--n-height) / 3) 0 calc(var(--n-height) / 2);
 `)]),u("disabled",`
 cursor: not-allowed !important;
 opacity: var(--n-opacity-disabled);
 `),u("checkable",`
 cursor: pointer;
 box-shadow: none;
 color: var(--n-text-color-checkable);
 background-color: var(--n-color-checkable);
 `,[I("disabled",[z("&:hover","background-color: var(--n-color-hover-checkable);",[I("checked","color: var(--n-text-color-hover-checkable);")]),z("&:active","background-color: var(--n-color-pressed-checkable);",[I("checked","color: var(--n-text-color-pressed-checkable);")])]),u("checked",`
 color: var(--n-text-color-checked);
 background-color: var(--n-color-checked);
 `,[I("disabled",[z("&:hover","background-color: var(--n-color-checked-hover);"),z("&:active","background-color: var(--n-color-checked-pressed);")])])])]),So=Object.assign(Object.assign(Object.assign({},K.props),Io),{bordered:{type:Boolean,default:void 0},checked:Boolean,checkable:Boolean,strong:Boolean,triggerClickOnClose:Boolean,onClose:[Array,Function],onMouseenter:Function,onMouseleave:Function,"onUpdate:checked":Function,onUpdateChecked:Function,internalCloseFocusable:{type:Boolean,default:!0},internalCloseIsButtonTag:{type:Boolean,default:!0},onCheckedChange:Function}),Bo=xo("n-tag"),$o=ho({name:"Tag",props:So,slots:Object,setup(c){const g=uo(null),{mergedBorderedRef:r,mergedClsPrefixRef:p,inlineThemeDisabled:a,mergedRtlRef:i,mergedComponentPropsRef:n}=bo(c),s=j(()=>{var o,l;return c.size||((l=(o=n==null?void 0:n.value)===null||o===void 0?void 0:o.Tag)===null||l===void 0?void 0:l.size)||"medium"}),t=K("Tag","-tag",zo,yo,c,p);ko(Bo,{roundRef:mo(c,"round")});function f(){if(!c.disabled&&c.checkable){const{checked:o,onCheckedChange:l,onUpdateChecked:C,"onUpdate:checked":h}=c;C&&C(!o),h&&h(!o),l&&l(!o)}}function k(o){if(c.triggerClickOnClose||o.stopPropagation(),!c.disabled){const{onClose:l}=c;l&&po(l,o)}}const b={setTextContent(o){const{value:l}=g;l&&(l.textContent=o)}},S=Co("Tag",i,p),P=j(()=>{const{type:o,color:{color:l,textColor:C}={}}=c,h=s.value,{common:{cubicBezierEaseInOut:B},self:{padding:H,closeMargin:$,borderRadius:R,opacityDisabled:M,textColorCheckable:T,textColorHoverCheckable:_,textColorPressedCheckable:E,textColorChecked:O,colorCheckable:w,colorHoverCheckable:W,colorPressedCheckable:V,colorChecked:L,colorCheckedHover:A,colorCheckedPressed:G,closeBorderRadius:J,fontWeightStrong:Q,[d("colorBordered",o)]:q,[d("closeSize",h)]:X,[d("closeIconSize",h)]:Y,[d("fontSize",h)]:Z,[d("height",h)]:F,[d("color",o)]:oo,[d("textColor",o)]:eo,[d("border",o)]:ro,[d("closeIconColor",o)]:N,[d("closeIconColorHover",o)]:lo,[d("closeIconColorPressed",o)]:co,[d("closeColorHover",o)]:ao,[d("closeColorPressed",o)]:no}}=t.value,y=fo($);return{"--n-font-weight-strong":Q,"--n-avatar-size-override":`calc(${F} - 8px)`,"--n-bezier":B,"--n-border-radius":R,"--n-border":ro,"--n-close-icon-size":Y,"--n-close-color-pressed":no,"--n-close-color-hover":ao,"--n-close-border-radius":J,"--n-close-icon-color":N,"--n-close-icon-color-hover":lo,"--n-close-icon-color-pressed":co,"--n-close-icon-color-disabled":N,"--n-close-margin-top":y.top,"--n-close-margin-right":y.right,"--n-close-margin-bottom":y.bottom,"--n-close-margin-left":y.left,"--n-close-size":X,"--n-color":l||(r.value?q:oo),"--n-color-checkable":w,"--n-color-checked":L,"--n-color-checked-hover":A,"--n-color-checked-pressed":G,"--n-color-hover-checkable":W,"--n-color-pressed-checkable":V,"--n-font-size":Z,"--n-height":F,"--n-opacity-disabled":M,"--n-padding":H,"--n-text-color":C||eo,"--n-text-color-checkable":T,"--n-text-color-checked":O,"--n-text-color-hover-checkable":_,"--n-text-color-pressed-checkable":E}}),v=a?vo("tag",j(()=>{let o="";const{type:l,color:{color:C,textColor:h}={}}=c;return o+=l[0],o+=s.value[0],C&&(o+=`a${D(C)}`),h&&(o+=`b${D(h)}`),r.value&&(o+="c"),o}),P,c):void 0;return Object.assign(Object.assign({},b),{rtlEnabled:S,mergedClsPrefix:p,contentRef:g,mergedBordered:r,handleClick:f,handleCloseClick:k,cssVars:a?void 0:P,themeClass:v==null?void 0:v.themeClass,onRender:v==null?void 0:v.onRender})},render(){var c,g;const{mergedClsPrefix:r,rtlEnabled:p,closable:a,color:{borderColor:i}={},round:n,onRender:s,$slots:t}=this;s==null||s();const f=U(t.avatar,b=>b&&x("div",{class:`${r}-tag__avatar`},b)),k=U(t.icon,b=>b&&x("div",{class:`${r}-tag__icon`},b));return x("div",{class:[`${r}-tag`,this.themeClass,{[`${r}-tag--rtl`]:p,[`${r}-tag--strong`]:this.strong,[`${r}-tag--disabled`]:this.disabled,[`${r}-tag--checkable`]:this.checkable,[`${r}-tag--checked`]:this.checkable&&this.checked,[`${r}-tag--round`]:n,[`${r}-tag--avatar`]:f,[`${r}-tag--icon`]:k,[`${r}-tag--closable`]:a}],style:this.cssVars,onClick:this.handleClick,onMouseenter:this.onMouseenter,onMouseleave:this.onMouseleave},k||f,x("span",{class:`${r}-tag__content`,ref:"contentRef"},(g=(c=this.$slots).default)===null||g===void 0?void 0:g.call(c)),!this.checkable&&a?x(go,{clsPrefix:r,class:`${r}-tag__close`,disabled:this.disabled,onClick:this.handleCloseClick,focusable:this.internalCloseFocusable,round:n,isButtonTag:this.internalCloseIsButtonTag,absolute:!0}):null,!this.checkable&&this.mergedBordered?x("div",{class:`${r}-tag__border`,style:{borderColor:i}}):null)}});export{$o as N};
