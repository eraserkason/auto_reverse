import{N as me,p as ge}from"./Popover-C07QE1g7.js";import{d as j,h as s,u as _,e as N,aU as ve,C as $,r as E,aN as A,aV as pe,a8 as q,a1 as we,S as J,aO as X,ai as ye,$ as Se,ae as $e,a7 as Ce,aW as ze,M as Z,aX as L,aY as xe,p as H,aZ as Be,a_ as Oe,a$ as Ee,b as i,b0 as D,c as b,a as S,K as B,b1 as Re,b2 as ke,b3 as Te,b4 as Pe,J as Me,b5 as Fe,b6 as He,O,b7 as je,P as Y,b8 as Ne,b9 as De}from"./index-CrjpUL23.js";import{u as V}from"./use-merged-state-GBKmWucP.js";import{f as K}from"./get-BgFtjOeo.js";const Ie=Object.assign(Object.assign({},ge),N.props),st=j({name:"Tooltip",props:Ie,slots:Object,__popover__:!0,setup(e){const{mergedClsPrefixRef:t}=_(e),r=N("Tooltip","-tooltip",void 0,ve,e,t),d=E(null);return Object.assign(Object.assign({},{syncPosition(){d.value.syncPosition()},setShow(v){d.value.setShow(v)}}),{popoverRef:d,mergedTheme:r,popoverThemeOverrides:$(()=>r.value.self)})},render(){const{mergedTheme:e,internalExtraClass:t}=this;return s(me,Object.assign(Object.assign({},this.$props),{theme:e.peers.Popover,themeOverrides:e.peerOverrides.Popover,builtinThemeOverrides:this.popoverThemeOverrides,internalExtraClass:t.concat("tooltip"),ref:"popoverRef"}),this.$slots)}}),We=j({name:"NDrawerContent",inheritAttrs:!1,props:{blockScroll:Boolean,show:{type:Boolean,default:void 0},displayDirective:{type:String,required:!0},placement:{type:String,required:!0},contentClass:String,contentStyle:[Object,String],nativeScrollbar:{type:Boolean,required:!0},scrollbarProps:Object,trapFocus:{type:Boolean,default:!0},autoFocus:{type:Boolean,default:!0},showMask:{type:[Boolean,String],required:!0},maxWidth:Number,maxHeight:Number,minWidth:Number,minHeight:Number,resizable:Boolean,onClickoutside:Function,onAfterLeave:Function,onAfterEnter:Function,onEsc:Function},setup(e){const t=E(!!e.show),r=E(null),d=Z(L);let f=0,v="",u=null;const p=E(!1),w=E(!1),C=$(()=>e.placement==="top"||e.placement==="bottom"),{mergedClsPrefixRef:R,mergedRtlRef:k}=_(e),T=ye("Drawer",k,R),z=o,m=n=>{w.value=!0,f=C.value?n.clientY:n.clientX,v=document.body.style.cursor,document.body.style.cursor=C.value?"ns-resize":"ew-resize",document.body.addEventListener("mousemove",y),document.body.addEventListener("mouseleave",z),document.body.addEventListener("mouseup",o)},M=()=>{u!==null&&(window.clearTimeout(u),u=null),w.value?p.value=!0:u=window.setTimeout(()=>{p.value=!0},300)},I=()=>{u!==null&&(window.clearTimeout(u),u=null),p.value=!1},{doUpdateHeight:W,doUpdateWidth:U}=d,P=n=>{const{maxWidth:l}=e;if(l&&n>l)return l;const{minWidth:h}=e;return h&&n<h?h:n},F=n=>{const{maxHeight:l}=e;if(l&&n>l)return l;const{minHeight:h}=e;return h&&n<h?h:n};function y(n){var l,h;if(w.value)if(C.value){let g=((l=r.value)===null||l===void 0?void 0:l.offsetHeight)||0;const x=f-n.clientY;g+=e.placement==="bottom"?x:-x,g=F(g),W(g),f=n.clientY}else{let g=((h=r.value)===null||h===void 0?void 0:h.offsetWidth)||0;const x=f-n.clientX;g+=e.placement==="right"?x:-x,g=P(g),U(g),f=n.clientX}}function o(){w.value&&(f=0,w.value=!1,document.body.style.cursor=v,document.body.removeEventListener("mousemove",y),document.body.removeEventListener("mouseup",o),document.body.removeEventListener("mouseleave",z))}Se(()=>{e.show&&(t.value=!0)}),$e(()=>e.show,n=>{n||o()}),Ce(()=>{o()});const a=$(()=>{const{show:n}=e,l=[[X,n]];return e.showMask||l.push([xe,e.onClickoutside,void 0,{capture:!0}]),l});function c(){var n;t.value=!1,(n=e.onAfterLeave)===null||n===void 0||n.call(e)}return ze($(()=>e.blockScroll&&t.value)),H(Be,r),H(Oe,null),H(Ee,null),{bodyRef:r,rtlEnabled:T,mergedClsPrefix:d.mergedClsPrefixRef,isMounted:d.isMountedRef,mergedTheme:d.mergedThemeRef,displayed:t,transitionName:$(()=>({right:"slide-in-from-right-transition",left:"slide-in-from-left-transition",top:"slide-in-from-top-transition",bottom:"slide-in-from-bottom-transition"})[e.placement]),handleAfterLeave:c,bodyDirectives:a,handleMousedownResizeTrigger:m,handleMouseenterResizeTrigger:M,handleMouseleaveResizeTrigger:I,isDragging:w,isHoverOnResizeTrigger:p}},render(){const{$slots:e,mergedClsPrefix:t}=this;return this.displayDirective==="show"||this.displayed||this.show?A(s("div",{role:"none"},s(pe,{disabled:!this.showMask||!this.trapFocus,active:this.show,autoFocus:this.autoFocus,onEsc:this.onEsc},{default:()=>s(q,{name:this.transitionName,appear:this.isMounted,onAfterEnter:this.onAfterEnter,onAfterLeave:this.handleAfterLeave},{default:()=>A(s("div",we(this.$attrs,{role:"dialog",ref:"bodyRef","aria-modal":"true",class:[`${t}-drawer`,this.rtlEnabled&&`${t}-drawer--rtl`,`${t}-drawer--${this.placement}-placement`,this.isDragging&&`${t}-drawer--unselectable`,this.nativeScrollbar&&`${t}-drawer--native-scrollbar`]}),[this.resizable?s("div",{class:[`${t}-drawer__resize-trigger`,(this.isDragging||this.isHoverOnResizeTrigger)&&`${t}-drawer__resize-trigger--hover`],onMouseenter:this.handleMouseenterResizeTrigger,onMouseleave:this.handleMouseleaveResizeTrigger,onMousedown:this.handleMousedownResizeTrigger}):null,this.nativeScrollbar?s("div",{class:[`${t}-drawer-content-wrapper`,this.contentClass],style:this.contentStyle,role:"none"},e):s(J,Object.assign({},this.scrollbarProps,{contentStyle:this.contentStyle,contentClass:[`${t}-drawer-content-wrapper`,this.contentClass],theme:this.mergedTheme.peers.Scrollbar,themeOverrides:this.mergedTheme.peerOverrides.Scrollbar}),e)]),this.bodyDirectives)})})),[[X,this.displayDirective==="if"||this.displayed||this.show]]):null}}),{cubicBezierEaseIn:Ue,cubicBezierEaseOut:Ae}=D;function _e({duration:e="0.3s",leaveDuration:t="0.2s",name:r="slide-in-from-bottom"}={}){return[i(`&.${r}-transition-leave-active`,{transition:`transform ${t} ${Ue}`}),i(`&.${r}-transition-enter-active`,{transition:`transform ${e} ${Ae}`}),i(`&.${r}-transition-enter-to`,{transform:"translateY(0)"}),i(`&.${r}-transition-enter-from`,{transform:"translateY(100%)"}),i(`&.${r}-transition-leave-from`,{transform:"translateY(0)"}),i(`&.${r}-transition-leave-to`,{transform:"translateY(100%)"})]}const{cubicBezierEaseIn:Le,cubicBezierEaseOut:Xe}=D;function Ye({duration:e="0.3s",leaveDuration:t="0.2s",name:r="slide-in-from-left"}={}){return[i(`&.${r}-transition-leave-active`,{transition:`transform ${t} ${Le}`}),i(`&.${r}-transition-enter-active`,{transition:`transform ${e} ${Xe}`}),i(`&.${r}-transition-enter-to`,{transform:"translateX(0)"}),i(`&.${r}-transition-enter-from`,{transform:"translateX(-100%)"}),i(`&.${r}-transition-leave-from`,{transform:"translateX(0)"}),i(`&.${r}-transition-leave-to`,{transform:"translateX(-100%)"})]}const{cubicBezierEaseIn:Ve,cubicBezierEaseOut:Ke}=D;function qe({duration:e="0.3s",leaveDuration:t="0.2s",name:r="slide-in-from-right"}={}){return[i(`&.${r}-transition-leave-active`,{transition:`transform ${t} ${Ve}`}),i(`&.${r}-transition-enter-active`,{transition:`transform ${e} ${Ke}`}),i(`&.${r}-transition-enter-to`,{transform:"translateX(0)"}),i(`&.${r}-transition-enter-from`,{transform:"translateX(100%)"}),i(`&.${r}-transition-leave-from`,{transform:"translateX(0)"}),i(`&.${r}-transition-leave-to`,{transform:"translateX(100%)"})]}const{cubicBezierEaseIn:Je,cubicBezierEaseOut:Ze}=D;function Ge({duration:e="0.3s",leaveDuration:t="0.2s",name:r="slide-in-from-top"}={}){return[i(`&.${r}-transition-leave-active`,{transition:`transform ${t} ${Je}`}),i(`&.${r}-transition-enter-active`,{transition:`transform ${e} ${Ze}`}),i(`&.${r}-transition-enter-to`,{transform:"translateY(0)"}),i(`&.${r}-transition-enter-from`,{transform:"translateY(-100%)"}),i(`&.${r}-transition-leave-from`,{transform:"translateY(0)"}),i(`&.${r}-transition-leave-to`,{transform:"translateY(-100%)"})]}const Qe=i([b("drawer",`
 word-break: break-word;
 line-height: var(--n-line-height);
 position: absolute;
 pointer-events: all;
 box-shadow: var(--n-box-shadow);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 background-color: var(--n-color);
 color: var(--n-text-color);
 box-sizing: border-box;
 `,[qe(),Ye(),Ge(),_e(),S("unselectable",`
 user-select: none; 
 -webkit-user-select: none;
 `),S("native-scrollbar",[b("drawer-content-wrapper",`
 overflow: auto;
 height: 100%;
 `)]),B("resize-trigger",`
 position: absolute;
 background-color: #0000;
 transition: background-color .3s var(--n-bezier);
 `,[S("hover",`
 background-color: var(--n-resize-trigger-color-hover);
 `)]),b("drawer-content-wrapper",`
 box-sizing: border-box;
 `),b("drawer-content",`
 height: 100%;
 display: flex;
 flex-direction: column;
 `,[S("native-scrollbar",[b("drawer-body-content-wrapper",`
 height: 100%;
 overflow: auto;
 `)]),b("drawer-body",`
 flex: 1 0 0;
 overflow: hidden;
 `),b("drawer-body-content-wrapper",`
 box-sizing: border-box;
 padding: var(--n-body-padding);
 `),b("drawer-header",`
 font-weight: var(--n-title-font-weight);
 line-height: 1;
 font-size: var(--n-title-font-size);
 color: var(--n-title-text-color);
 padding: var(--n-header-padding);
 transition: border .3s var(--n-bezier);
 border-bottom: 1px solid var(--n-divider-color);
 border-bottom: var(--n-header-border-bottom);
 display: flex;
 justify-content: space-between;
 align-items: center;
 `,[B("main",`
 flex: 1;
 `),B("close",`
 margin-left: 6px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `)]),b("drawer-footer",`
 display: flex;
 justify-content: flex-end;
 border-top: var(--n-footer-border-top);
 transition: border .3s var(--n-bezier);
 padding: var(--n-footer-padding);
 `)]),S("right-placement",`
 top: 0;
 bottom: 0;
 right: 0;
 border-top-left-radius: var(--n-border-radius);
 border-bottom-left-radius: var(--n-border-radius);
 `,[B("resize-trigger",`
 width: 3px;
 height: 100%;
 top: 0;
 left: 0;
 transform: translateX(-1.5px);
 cursor: ew-resize;
 `)]),S("left-placement",`
 top: 0;
 bottom: 0;
 left: 0;
 border-top-right-radius: var(--n-border-radius);
 border-bottom-right-radius: var(--n-border-radius);
 `,[B("resize-trigger",`
 width: 3px;
 height: 100%;
 top: 0;
 right: 0;
 transform: translateX(1.5px);
 cursor: ew-resize;
 `)]),S("top-placement",`
 top: 0;
 left: 0;
 right: 0;
 border-bottom-left-radius: var(--n-border-radius);
 border-bottom-right-radius: var(--n-border-radius);
 `,[B("resize-trigger",`
 width: 100%;
 height: 3px;
 bottom: 0;
 left: 0;
 transform: translateY(1.5px);
 cursor: ns-resize;
 `)]),S("bottom-placement",`
 left: 0;
 bottom: 0;
 right: 0;
 border-top-left-radius: var(--n-border-radius);
 border-top-right-radius: var(--n-border-radius);
 `,[B("resize-trigger",`
 width: 100%;
 height: 3px;
 top: 0;
 left: 0;
 transform: translateY(-1.5px);
 cursor: ns-resize;
 `)])]),i("body",[i(">",[b("drawer-container",`
 position: fixed;
 `)])]),b("drawer-container",`
 position: relative;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 pointer-events: none;
 `,[i("> *",`
 pointer-events: all;
 `)]),b("drawer-mask",`
 background-color: rgba(0, 0, 0, .3);
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `,[S("invisible",`
 background-color: rgba(0, 0, 0, 0)
 `),Re({enterDuration:"0.2s",leaveDuration:"0.2s",enterCubicBezier:"var(--n-bezier-in)",leaveCubicBezier:"var(--n-bezier-out)"})])]),et=Object.assign(Object.assign({},N.props),{show:Boolean,width:[Number,String],height:[Number,String],placement:{type:String,default:"right"},maskClosable:{type:Boolean,default:!0},showMask:{type:[Boolean,String],default:!0},to:[String,Object],displayDirective:{type:String,default:"if"},nativeScrollbar:{type:Boolean,default:!0},zIndex:Number,onMaskClick:Function,scrollbarProps:Object,contentClass:String,contentStyle:[Object,String],trapFocus:{type:Boolean,default:!0},onEsc:Function,autoFocus:{type:Boolean,default:!0},closeOnEsc:{type:Boolean,default:!0},blockScroll:{type:Boolean,default:!0},maxWidth:Number,maxHeight:Number,minWidth:Number,minHeight:Number,resizable:Boolean,defaultWidth:{type:[Number,String],default:251},defaultHeight:{type:[Number,String],default:251},onUpdateWidth:[Function,Array],onUpdateHeight:[Function,Array],"onUpdate:width":[Function,Array],"onUpdate:height":[Function,Array],"onUpdate:show":[Function,Array],onUpdateShow:[Function,Array],onAfterEnter:Function,onAfterLeave:Function,drawerStyle:[String,Object],drawerClass:String,target:null,onShow:Function,onHide:Function}),at=j({name:"Drawer",inheritAttrs:!1,props:et,setup(e){const{mergedClsPrefixRef:t,namespaceRef:r,inlineThemeDisabled:d}=_(e),f=Te(),v=N("Drawer","-drawer",Qe,je,e,t),u=E(e.defaultWidth),p=E(e.defaultHeight),w=V(Y(e,"width"),u),C=V(Y(e,"height"),p),R=$(()=>{const{placement:o}=e;return o==="top"||o==="bottom"?"":K(w.value)}),k=$(()=>{const{placement:o}=e;return o==="left"||o==="right"?"":K(C.value)}),T=o=>{const{onUpdateWidth:a,"onUpdate:width":c}=e;a&&O(a,o),c&&O(c,o),u.value=o},z=o=>{const{onUpdateHeight:a,"onUpdate:width":c}=e;a&&O(a,o),c&&O(c,o),p.value=o},m=$(()=>[{width:R.value,height:k.value},e.drawerStyle||""]);function M(o){const{onMaskClick:a,maskClosable:c}=e;c&&P(!1),a&&a(o)}function I(o){M(o)}const W=Pe();function U(o){var a;(a=e.onEsc)===null||a===void 0||a.call(e),e.show&&e.closeOnEsc&&He(o)&&(W.value||P(!1))}function P(o){const{onHide:a,onUpdateShow:c,"onUpdate:show":n}=e;c&&O(c,o),n&&O(n,o),a&&!o&&O(a,o)}H(L,{isMountedRef:f,mergedThemeRef:v,mergedClsPrefixRef:t,doUpdateShow:P,doUpdateHeight:z,doUpdateWidth:T});const F=$(()=>{const{common:{cubicBezierEaseInOut:o,cubicBezierEaseIn:a,cubicBezierEaseOut:c},self:{color:n,textColor:l,boxShadow:h,lineHeight:g,headerPadding:x,footerPadding:G,borderRadius:Q,bodyPadding:ee,titleFontSize:te,titleTextColor:re,titleFontWeight:oe,headerBorderBottom:ne,footerBorderTop:ie,closeIconColor:se,closeIconColorHover:ae,closeIconColorPressed:le,closeColorHover:de,closeColorPressed:ce,closeIconSize:ue,closeSize:he,closeBorderRadius:fe,resizableTriggerColorHover:be}}=v.value;return{"--n-line-height":g,"--n-color":n,"--n-border-radius":Q,"--n-text-color":l,"--n-box-shadow":h,"--n-bezier":o,"--n-bezier-out":c,"--n-bezier-in":a,"--n-header-padding":x,"--n-body-padding":ee,"--n-footer-padding":G,"--n-title-text-color":re,"--n-title-font-size":te,"--n-title-font-weight":oe,"--n-header-border-bottom":ne,"--n-footer-border-top":ie,"--n-close-icon-color":se,"--n-close-icon-color-hover":ae,"--n-close-icon-color-pressed":le,"--n-close-size":he,"--n-close-color-hover":de,"--n-close-color-pressed":ce,"--n-close-icon-size":ue,"--n-close-border-radius":fe,"--n-resize-trigger-color-hover":be}}),y=d?Me("drawer",void 0,F,e):void 0;return{mergedClsPrefix:t,namespace:r,mergedBodyStyle:m,handleOutsideClick:I,handleMaskClick:M,handleEsc:U,mergedTheme:v,cssVars:d?void 0:F,themeClass:y==null?void 0:y.themeClass,onRender:y==null?void 0:y.onRender,isMounted:f}},render(){const{mergedClsPrefix:e}=this;return s(ke,{to:this.to,show:this.show},{default:()=>{var t;return(t=this.onRender)===null||t===void 0||t.call(this),A(s("div",{class:[`${e}-drawer-container`,this.namespace,this.themeClass],style:this.cssVars,role:"none"},this.showMask?s(q,{name:"fade-in-transition",appear:this.isMounted},{default:()=>this.show?s("div",{"aria-hidden":!0,class:[`${e}-drawer-mask`,this.showMask==="transparent"&&`${e}-drawer-mask--invisible`],onClick:this.handleMaskClick}):null}):null,s(We,Object.assign({},this.$attrs,{class:[this.drawerClass,this.$attrs.class],style:[this.mergedBodyStyle,this.$attrs.style],blockScroll:this.blockScroll,contentStyle:this.contentStyle,contentClass:this.contentClass,placement:this.placement,scrollbarProps:this.scrollbarProps,show:this.show,displayDirective:this.displayDirective,nativeScrollbar:this.nativeScrollbar,onAfterEnter:this.onAfterEnter,onAfterLeave:this.onAfterLeave,trapFocus:this.trapFocus,autoFocus:this.autoFocus,resizable:this.resizable,maxHeight:this.maxHeight,minHeight:this.minHeight,maxWidth:this.maxWidth,minWidth:this.minWidth,showMask:this.showMask,onEsc:this.handleEsc,onClickoutside:this.handleOutsideClick}),this.$slots)),[[Fe,{zIndex:this.zIndex,enabled:this.show}]])}})}}),tt={title:String,headerClass:String,headerStyle:[Object,String],footerClass:String,footerStyle:[Object,String],bodyClass:String,bodyStyle:[Object,String],bodyContentClass:String,bodyContentStyle:[Object,String],nativeScrollbar:{type:Boolean,default:!0},scrollbarProps:Object,closable:Boolean},lt=j({name:"DrawerContent",props:tt,slots:Object,setup(){const e=Z(L,null);e||De("drawer-content","`n-drawer-content` must be placed inside `n-drawer`.");const{doUpdateShow:t}=e;function r(){t(!1)}return{handleCloseClick:r,mergedTheme:e.mergedThemeRef,mergedClsPrefix:e.mergedClsPrefixRef}},render(){const{title:e,mergedClsPrefix:t,nativeScrollbar:r,mergedTheme:d,bodyClass:f,bodyStyle:v,bodyContentClass:u,bodyContentStyle:p,headerClass:w,headerStyle:C,footerClass:R,footerStyle:k,scrollbarProps:T,closable:z,$slots:m}=this;return s("div",{role:"none",class:[`${t}-drawer-content`,r&&`${t}-drawer-content--native-scrollbar`]},m.header||e||z?s("div",{class:[`${t}-drawer-header`,w],style:C,role:"none"},s("div",{class:`${t}-drawer-header__main`,role:"heading","aria-level":"1"},m.header!==void 0?m.header():e),z&&s(Ne,{onClick:this.handleCloseClick,clsPrefix:t,class:`${t}-drawer-header__close`,absolute:!0})):null,r?s("div",{class:[`${t}-drawer-body`,f],style:v,role:"none"},s("div",{class:[`${t}-drawer-body-content-wrapper`,u],style:p,role:"none"},m)):s(J,Object.assign({themeOverrides:d.peerOverrides.Scrollbar,theme:d.peers.Scrollbar},T,{class:`${t}-drawer-body`,contentClass:[`${t}-drawer-body-content-wrapper`,u],contentStyle:p}),m),m.footer?s("div",{class:[`${t}-drawer-footer`,R],style:k,role:"none"},m.footer()):null)}});export{st as N,lt as a,at as b};
